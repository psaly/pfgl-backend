#!/bin/zsh
# copy the pod name of the pfgl pod on okteto (must be in okteto cloud kubectl context)
kubectl get pods | grep pfgl | cut -d " " -f 1 | pbcopy
