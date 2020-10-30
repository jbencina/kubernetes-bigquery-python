kubectl create -f bigquery-controller.yaml
kubectl create -f twitter-stream.yaml
kubectl get pods  -o wide