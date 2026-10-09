# OpenShift GitOps

Three charts, applied in order.

`ocp/setup-project` creates the data science project from `ocp/setup/values.yaml`, an Argo CD instance in that project and the Application `data-science-onboarding`.

`ocp/setup-registry` creates the model registry in `rhoai-model-registries`.

`data-science-onboarding` is what that Application syncs, together with `mlops/tekton/s3`. It creates the NooBaa claims, the Jobs that publish OpenShift AI connections, and the `dspa` pipeline server.

`ocp/setup.sh` is the script to install the `openshift-gitops` ArgoCD instance and the respective ArgoCD applications.
