 wget -O- https://carvel.dev/install.sh > install.sh
 
 sudo bash install.sh
 
 ytt version
 
#@ load("@ytt:overlay", "overlay")

#@overlay/match by=overlay.subset({"kind": "Service", "spec":{"type":"LoadBalancer"}}),expects=1
---
spec:
  #@overlay/replace
  type: NodePort

ytt -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud/deploy.yaml \
-f convert-lb-to-nodeport.yaml \
--ignore-unknown-comments=true | kubectl apply -f -

kubectl apply -f ingress.yaml

ytt -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud/deploy.yaml \
-f daemon-set.yaml \
-f convert-lb-to-nodeport.yaml \
--ignore-unknown-comments=true | kubectl apply -f -


kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml

apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
  namespace: cert-manager
spec:
  acme:
    email: user@example.com
    privateKeySecretRef:
      name: letsencrypt-staging
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    solvers:
    - http01:
        ingress:
          class: contour
          
kubectl apply -f letsencrypt-staging.yaml

root@master:~/contour# kubectl get clusterissuer letsencrypt-staging
NAME                  READY   AGE
letsencrypt-staging   True    79s

apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  namespace: cert-manager
spec:
  acme:
    email: samokhin@shockland.ru
    privateKeySecretRef:
      name: letsencrypt-prod
    server: https://acme-v02.api.letsencrypt.org/directory
    solvers:
    - http01:
        ingress:
          class: contour

kubectl edit ingress django-ingress

spec:
  ingressClassName: nginx


