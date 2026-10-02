# OpenShift GitOps

Two charts, applied in order.

`ocp/setup` creates the data science project from `ocp/setup/values.yaml`, an Argo CD instance in that project, the model registry in `rhoai-model-registries`, and the Application `data-science-onboarding`.

`data-science-onboarding` is what that Application syncs, together with `mlops/tekton/s3`. It creates the NooBaa claims, the Jobs that publish OpenShift AI connections, and the `dspa` pipeline server.

`ocp/application.yaml` is the Application in `openshift-gitops` that tracks this repository.
