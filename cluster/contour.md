 ## Установка и настройка Ingress-контроллера
 
 Устанавлиаем утилиту ytt для патча манифестов:
```
wget -O- https://carvel.dev/install.sh > install.sh
sudo bash install.sh
ytt version
```
Устанавливаем ingress-контроллер в режиме DaemonSet и типе NodePort:
```
ytt -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud/deploy.yaml \
-f daemon-set.yaml \
-f convert-lb-to-nodeport.yaml \
--ignore-unknown-comments=true | kubectl apply -f -
```

```sh
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml
kubectl apply -f letsencrypt-staging.yaml
```
```
kubectl get clusterissuer letsencrypt-staging
```
```console
NAME                  READY   AGE
letsencrypt-staging   True    79s
```

```sh
kubectl apply -f cluster\ingress.yaml
```

После того, как сертификат будет получен от `staging` сервера, заменяем его на `prod`.  Создаем новый `clusterissuer`
```sh
kubectl apply -f letsencrypt-prod.yaml
```
И редактируем `ingress` заменив  
.metadata.annotations.cert-manager.io/cluster-issuer: ~~letsencrypt-staging~~ letsencrypt-prod  

У меня возникла проблема при выпуске сертификата, при проверке права владения доменным именем не работал `solver` пока в него не добавить:
```
spec:
  ingressClassName: nginx
```

