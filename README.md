# Django site

Докеризированный сайт на Django для экспериментов с Kubernetes.

Внутри контейнера Django запускается с помощью Nginx Unit, не путать с Nginx. Сервер Nginx Unit выполняет сразу две функции: как веб-сервер он раздаёт файлы статики и медиа, а в роли сервера-приложений он запускает Python и Django. Таким образом Nginx Unit заменяет собой связку из двух сервисов Nginx и Gunicorn/uWSGI. [Подробнее про Nginx Unit](https://unit.nginx.org/).

## Как запустить dev-версию

Запустите базу данных и сайт:

```shell-session
$ docker-compose up
```

В новом терминале не выключая сайт запустите команды для настройки базы данных:

```shell-session
$ docker-compose run web ./manage.py migrate  # создаём/обновляем таблицы в БД
$ docker-compose run web ./manage.py createsuperuser
```

Для тонкой настройки Docker Compose используйте переменные окружения. Их названия отличаются от тех, что задаёт docker-образа, сделано это чтобы избежать конфликта имён. Внутри docker-compose.yaml настраиваются сразу несколько образов, у каждого свои переменные окружения, и поэтому их названия могут случайно пересечься. Чтобы не было конфликтов к названиям переменных окружения добавлены префиксы по названию сервиса. Список доступных переменных можно найти внутри файла [`docker-compose.yml`](./docker-compose.yml).

## Переменные окружения

Образ с Django считывает настройки из переменных окружения:

`SECRET_KEY` -- обязательная секретная настройка Django. Это соль для генерации хэшей. Значение может быть любым, важно лишь, чтобы оно никому не было известно. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key).

`DEBUG` -- настройка Django для включения отладочного режима. Принимает значения `TRUE` или `FALSE`. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#std:setting-DEBUG).

`ALLOWED_HOSTS` -- настройка Django со списком разрешённых адресов. Если запрос прилетит на другой адрес, то сайт ответит ошибкой 400. Можно перечислить несколько адресов через запятую, например `127.0.0.1,192.168.0.1,site.test`. [Документация Django](https://docs.djangoproject.com/en/3.2/ref/settings/#allowed-hosts).

`DATABASE_URL` -- адрес для подключения к базе данных PostgreSQL. Другие СУБД сайт не поддерживает. [Формат записи](https://github.com/jacobian/dj-database-url#url-schema).



## Развертывание в Minikube

[Инструкции](https://minikube.sigs.k8s.io/docs/start/) по установке Minikube на локальную машину.  
Для развертывания PostgreSQL понадобится менеджер пакетов Kubernetes - [Helm](https://helm.sh/docs/intro/install/), для управления кластером Minikube утилита - [kubectl](https://kubernetes.io/ru/docs/tasks/tools/install-kubectl/)

Запускаем кластер Kubernetes в Minikube:  
```sh
minikube start --driver=virtualbox
```
Дожидаемся окончания выполнения команды и проверяем, что кластер успешно развернут:
```sh
kubectl get all --all-namespaces
```
В результате должны получить подобный вывод:
```
NAMESPACE     NAME                                   READY   STATUS    RESTARTS      AGE
kube-system   pod/coredns-565d847f94-zts7r           1/1     Running   0             22m
kube-system   pod/etcd-minikube                      1/1     Running   0             22m
kube-system   pod/kube-apiserver-minikube            1/1     Running   0             22m
kube-system   pod/kube-controller-manager-minikube   1/1     Running   0             22m
kube-system   pod/kube-proxy-4vjvd                   1/1     Running   0             22m
kube-system   pod/kube-scheduler-minikube            1/1     Running   0             22m
kube-system   pod/storage-provisioner                1/1     Running   1 (21m ago)   22m

NAMESPACE     NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)                  AGE
default       service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP                  22m
kube-system   service/kube-dns     ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP,9153/TCP   22m

NAMESPACE     NAME                        DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
kube-system   daemonset.apps/kube-proxy   1         1         1       1            1           kubernetes.io/os=linux   22m

NAMESPACE     NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
kube-system   deployment.apps/coredns   1/1     1            1           22m

NAMESPACE     NAME                                 DESIRED   CURRENT   READY   AGE
kube-system   replicaset.apps/coredns-565d847f94   1         1         1       22m
```
Убеждаемся, что все наши сервисы в состоянии `READY`, статус `Running` и нет сообщений об ошибках.

### Устанавливаем базу данных PostgreSQL.  
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install db --set commonLabels='app.kubernetes.io/part-of: django-application-k8s-example' bitnami/postgresql
```
В выводе второй команды находим следущие строки:
```
`PostgreSQL can be accessed via port 5432 on the following DNS names from within your cluster:

    db-postgresql.default.svc.cluster.local - Read/Write connection
```
`db-postgresql` - это имя созданного сервиса, к нему можно обращаться по имени внутри кластера.  
Теперь мы можем создать особую сущность Kubernetes - `secret`. В ней будут хранится секретные даннные, такие как логины, пароли и т.п.  
  ```bash
  kubectl create secret generic django-secret-v1 --from-literal='SECRET_KEY=67wi5rqyv(aynrrwcxlq25@_(83*6)9s##(rz4hi=+0b&1%-e&' --from-literal='DATABASE_URL=postgres://starburger_db_user:password@db-postgresql:5432/star_burger'
 ```
Учетные данные, указанные в `DATABASE_URL` мы будем использовать при создании БД через `psql`  
Находим имя пода с инcтансом PostgreSQL:  
```
kubectl get po -l app.kubernetes.io/instance=db
```
```
NAME              READY   STATUS    RESTARTS   AGE
db-postgresql-0   1/1     Running   0          63m
```
И затем подключаемся к нему:
```sh
kubectl exec db-postgresql-0 -it -- bash
```
Подключаемся к Postgres внутри pod:
```
psql postgres://postgres:${POSTGRES_PASSWORD}@
```
Создаем базу данных проекта:
```
postgres=# CREATE DATABASE star_burger;
```
Создаем пользователя, через которого будем подключаться к БД, используя учетные данные указанные в `secret`:
```
postgres=# CREATE USER starburger_db_user WITH PASSWORD 'password';
```
Делаем необходимые настройки:
```
postgres=# ALTER ROLE starburger_db_user SET client_encoding TO 'utf8';
postgres=# ALTER ROLE starburger_db_user SET default_transaction_isolation TO 'read committed';
postgres=# ALTER ROLE starburger_db_user SET timezone TO 'UTC';
```
Даем права нашему пользователю на созданную базу:
```
postgres=# GRANT ALL PRIVILEGES ON DATABASE star_burger TO starburger_db_user;
```
Подключаемся к созданной базе:
```
postgres=#\c star_burger;
```
и обновляем права:
```
star_burger=#GRANT ALL ON SCHEMA public TO starburger_db_user;
```
### Развертываем Django

Создаем ConfigMap в кластере командой:
```sh
kubectl apply -f minikube/env.yaml
```
Проверяем, что сущность создалась:
```sh
kubectl describe cm django-configmap-v1
```
Команда должна вывести на экран пары ключи:значения из нашего файла.  

Построение образа приложения:

```sh
minikube image build -t dj:fresh backend_main_django/
```
Дожидаемся завершения и провеяем, что образ локально доступен minikube:
```
minikube image ls
```
Среди списка образов должен быть `dj:fresh`  
Теперь можно развернуть приложение с помощью deployment, использующего этот образ:
```sh
kubectl apply -f minikube/django-deploy.yaml
```
Проверяем, что успешно появились pod, deployment, replicaset, service:
```
kubectl get all -l app.kubernetes.io/part-of=django-application-k8s-example
```
```
NAME                               READY   STATUS    RESTARTS   AGE
pod/db-postgresql-0                1/1     Running   0          55m
pod/django-unit-5796964776-q6jk9   1/1     Running   0          3m3s

NAME                             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/db-postgresql            ClusterIP   10.110.201.75    <none>        5432/TCP   55m
service/db-postgresql-hl         ClusterIP   None             <none>        5432/TCP   55m
service/django-unit-cluster-ip   ClusterIP   10.100.115.113   <none>        8080/TCP   3m3s

NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/django-unit   1/1     1            1           3m3s

NAME                                     DESIRED   CURRENT   READY   AGE
replicaset.apps/django-unit-5796964776   1         1         1       3m3s

NAME                             READY   AGE
statefulset.apps/db-postgresql   1/1     55m
```
Теперь обеспечим доступ к нашему приложению снаружи кластера через Ingress. Активируем встроенный add-on в minikube:
```sh
minikube addons enable ingress
```
Развертываем nginx-ingress:
```sh
kubectl apply -f minikube/ingress.yaml
```
Узнаем внешний адрес нашего кластера minikube:
```
minikube ip
```
Добавляем полученный ip-адрес и имя `star-burger.test` в файл `hosts` нашего компьютера, например:
```
192.168.49.2    star-burger.test
```
Теперь мы можем набрать адрес `http://star-burger.test` в браузере и должна открыться страница входа в админку Django.  
Теперь подключаемся к pod c Django:
```sh
kubectl exec pod/django-unit-5d9bf96bcb-kgwg5 -it -- bash

```
Делаем миграции и создаем админа:
```sh
python manage.py migrate
python manage.py createsuperuser
```
Базовая настройка нашего приложения закончена. В дальшейшем для выполнения команды `migrate` можно использовать заранее созданный job:
```sh
kubectl -f apply django-unit/django-migrate
```
А для регулярного удаления сессий, создать расписание:
```sh
kubectl apply -f django-unit/cron-job.yaml
```
## Деплой в кластере kubernetes

Установка и настройка кластера на VPS в файлах: [cluster\k8s.md](https://raw.githubusercontent.com/Corwin74/k8s-test-django/main/cluster/contour.md) и [cluster\contour.md](https://raw.githubusercontent.com/Corwin74/k8s-test-django/main/cluster/contour.md)

Для работы приложения необходим `secret django-secret-v1`, содержащий url подключения в котором приложению передаются учетные данные для подключения к базе данных, и SECRET_KEY для Django.
```
kubectl create secret generic django-secret-v1 --from-literal='SECRET_KEY=67wi5rqyv(aynrrwcxlq25@_(83*6)9s##(rz4hi=+0b&1%-e&' --from-literal='DATABASE_URL=postgres://starburger_db_user:password@db-postgresql:5432/star_burger'
```

Переменные окружения `ALLOWED_HOSTS` считываются из `config map ` `django-configmap-v1`
Образец для создания манифеста в файле `kubernetes/env.yaml`

Образ приложения хранится в Docker Registry: `corwinz/dj`

Образец манифеста для развертывания в кластере: `cluster\django-deploy.yaml`  

#### Сборка образа

Переходим в каталог `backend_main_django` и выполняем команду `make build`
```sh
cd backend_main_django
make build
```
После успешной сборки отправляем образ в Docker Registry
```sh
make push
```
В кластере мы можем изменить образ используемый нашим приложением на более свежий или откатиться на предыдущий командой `kubectl set image`, указав нужный тег образа:

```sh
kubectl set image deployments django-unit django=corwinz/dj:480a8be
```
Этот образ содержит изменение, в котором приложение по адресу: https://k8s.shockland.ru/secret отвечает `Badams!!!`, а если заменить образ на предыдущий:  
```sh
kubectl set image deployments django-unit django=corwinz/dj:a075d38
```
То по этому же адресу получим ошибку `404. Not found`  
Для просмотра логов приложения используем команду `kubectl logs`, заменив имя пода на актуальное:
```sh
kubectl logs django-unit-6fcfb9db55-tcgks
```
