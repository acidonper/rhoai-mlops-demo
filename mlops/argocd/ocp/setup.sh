#!/bin/bash

# Install ArgoCD Operator
oc create ns openshift-gitops-operator
oc create ns project01
oc label namespace openshift-gitops-operator argocd.argoproj.io/managed-by=openshift-gitops
oc apply -f 00-GitOps-Operator.yaml
sleep 60

# Install ArgoCD Application
oc apply -f 01-application-project.yaml

# Install ArgoCD Application
oc apply -f 02-application-registry.yaml

# Label the namespaces
oc label namespace rhoai-model-registries argocd.argoproj.io/managed-by=openshift-gitops
oc label namespace project01 argocd.argoproj.io/managed-by=openshift-gitops
oc create clusterrolebinding openshift-gitops-argocd-application-controller-cluster-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=openshift-gitops:openshift-gitops-argocd-application-controller