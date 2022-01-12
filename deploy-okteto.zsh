#!/bin/zsh
docker build . -t piercesaly/pfgl:latest
docker push piercesaly/pfgl:latest
./pfgl-podname.zsh
kubectl delete pod `pbpaste`
