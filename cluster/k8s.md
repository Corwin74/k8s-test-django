# Настройка кластера kubernetes на облачных VPS  
Арендуем два VPS сервера. с возможностью объединения их в частную сеть на стороне облака. Конфигурация: минимум 2 vCPU, 1Gb памяти.

Даем серверам имена:
```sh
hostnamectl set-hostname master.local
hostnamectl set-hostname worker.local
```
Редактируем /etc/hosts на обоих серверах.

10.0.0.11 master.local
10.0.0.12 worker.local

### Настройка автозагрузки и запуск модуля ядра br_netfilter и overlay
```sh
cat <<EOF | tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
```
```console
modprobe overlay
modprobe br_netfilter
```
### Разрешение маршрутизации IP-трафика
```sh
echo -e "net.bridge.bridge-nf-call-ip6tables = 1\nnet.bridge.bridge-nf-call-iptables = 1\nnet.ipv4.ip_forward = 1" > /etc/sysctl.d/10-k8s.conf
sysctl -f /etc/sysctl.d/10-k8s.conf
```
### Отключение файла подкачки
```sh
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab
```
Проверяем настройки:  
```sh
lsmod | grep br_netfilter
lsmod | grep overlay
```
Ожидаемый результат должен быть следующим (цифры могут отличаться):
```console
br_netfilter           32768  0
bridge                258048  1 br_netfilter
overlay               147456  0
```
```sh
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward
```
Ожидаемый результат:
```console
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
```
```sh
swapon -s
```
Ожидаемый вывод команды – пустой. Она ничего не должна отобразить.

### Настройка deb-репозитория Kubernetes
```sh
curl -fsSLo /etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/etc/apt/trusted.gpg.d/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
```
#### Обновление перечня доступных пакетов
```sh
apt update
```
#### Установка пакетов kubeadm и kubectl
```sh
apt install -y kubeadm kubectl
```
### Установка контейнерного движка

#### Установка containerd
```sh
wget https://github.com/containerd/containerd/releases/download/v1.7.0/containerd-1.7.0-linux-amd64.tar.gz
tar Cxzvf /usr/local containerd-1.7.0-linux-amd64.tar.gz
rm containerd-1.7.0-linux-amd64.tar.gz
```
#### Создание конфигурации по умолчанию для containerd
```sh
mkdir /etc/containerd/
containerd config default > /etc/containerd/config.toml
```
#### Настройка cgroup драйвера
```sh
sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
```
#### Установка systemd сервиса для containerd
```sh
wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service
mv containerd.service /etc/systemd/system/
```
#### Установка компонента runc
```sh
wget https://github.com/opencontainers/runc/releases/download/v1.1.4/runc.amd64
install -m 755 runc.amd64 /usr/local/sbin/runc
rm runc.amd64
```
#### Установка сетевых плагинов:
```sh
wget https://github.com/containernetworking/plugins/releases/download/v1.2.0/cni-plugins-linux-amd64-v1.2.0.tgz
mkdir -p /opt/cni/bin
tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.2.0.tgz
rm cni-plugins-linux-amd64-v1.2.0.tgz
```
#### Запуск сервиса containerd
```sh
systemctl daemon-reload
systemctl enable --now containerd
```
Проверяем:  
```sh
crictl --runtime-endpoint unix:///var/run/containerd/containerd.sock version
```
Ожидаемый результат:
```console
Version:  0.1.0
RuntimeName:  containerd
RuntimeVersion:  v1.7.0
RuntimeApiVersion:  v1
```
```sh
ctr images pull docker.io/library/hello-world:latest
ctr run docker.io/library/hello-world:latest hello-world
```
Ожидаемый результат:
```console
 …
 Hello from Docker!
 This message shows that your installation appears to be working correctly.
 …
```
### Установка кластера kubernetes
```sh
kubeadm config images pull
kubeadm init --upload-certs --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint "10.0.0.11"                           
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```          
Вторая команда должна вывести подобную строку для подключения второй ноды в кластер:
```sh               
kubeadm join 10.0.0.12:6443 --token iv26hh.tjsy0iz0b2n22oy9 \
	--discovery-token-ca-cert-hash sha256:94ec6121d719eed9961b772de7d08318259261ae7b4c0d1dbf717611c128f6bf 
```
На управляющей ноде делаем настройки для корректной работы `kubectl`
```sh
echo "export KUBECONFIG=/etc/kubernetes/admin.conf" > /etc/environment
export KUBECONFIG=/etc/kubernetes/admin.conf
```
Поскольку у нас только две ноды, разрешаем выполнять полезную нагрузку на управляющей ноде:
```sh
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```
### Создание  storage:

```sh
sudo mkdir /mnt/pv_data
kubectl apply -f pv-volume.yaml
```
Проверяем:
```
kubectl get pv
```
```console
NAME        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS   REASON   AGE
db-volume   5Gi        RWO            Retain           Available           manual                  50s
```
```console
NAME          STATUS   VOLUME      CAPACITY   ACCESS MODES   STORAGECLASS   AGE
db-pv-claim   Bound    db-volume   5Gi        RWO            manual         6s

NAME        CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                 STORAGECLASS   REASON   AGE
db-volume   5Gi        RWO            Retain           Bound    default/db-pv-claim   manual                  4m13s
```
```sh
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
```

helm install db --set commonLabels='app.kubernetes.io/part-of: django-application-k8s-example' --set volumePermissions.enabled=true -f values.yaml bitnami/postgresql


