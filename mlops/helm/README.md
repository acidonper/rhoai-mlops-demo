# OpenShift GitOps

Three charts, applied in order.

`setup-project` creates the data science project from `setup-project/values.yaml`, an Argo CD instance in that project and the Application `data-science-onboarding`.

`setup-registry` creates the model registry in `rhoai-model-registries`.

`data-science-onboarding` is what that Application syncs, together with `mlops/tekton/s3`. It creates the NooBaa claims, the Jobs that publish OpenShift AI connections, and the `dspa` pipeline server.