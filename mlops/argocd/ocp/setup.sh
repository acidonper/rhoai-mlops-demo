#!/bin/bash

# Install ArgoCD Operator
oc apply -f 00-ArgoCD_Operator.yaml
sleep 60

# Install ArgoCD Application
oc apply -f 01-application-project.yaml

# Install ArgoCD Application
oc apply -f 02-application-registry.yaml

# Label the namespaces
oc label namespace rhoai-model-registries argocd.argoproj.io/managed-by=openshift-gitops
oc label namespace project01 argocd.argoproj.io/managed-by=openshift-gitops