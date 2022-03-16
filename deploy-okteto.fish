#!/usr/local/bin/fish
docker build . -t piercesaly/pfgl:latest
docker push piercesaly/pfgl:latest
./pfgl-podname.fish
kubectl delete pod (pbpaste)
