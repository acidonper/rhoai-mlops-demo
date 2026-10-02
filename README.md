# AI/ML Lifecycle with Red Hat OpenShift AI

This demonstration showcases an MLOps approach for establishing an AI/ML workflow alongside the key components required to execute this strategy:

- Configure ArgoCD to serve as a functional GitOps tool
- Set up OpenShift and Openshift AI onboarding mechanisms, including model registry, S3 integrations, and the DataSciencePipelinesApplication server
- Establish a dedicated workspace to build and deploy production-grade pipelines for platform researchers

## What gets installed

1. The `ocp-setup` chart in `mlops/argocd/ocp/setup` creates the OpenShift project, an Argo CD instance in that project, a MySQL-backed model registry, and the `data-science-onboarding` Application. The project name and git source are in `mlops/argocd/ocp/setup/values.yaml`.
2. That Application syncs two paths into the project namespace:
   - `mlops/tekton/s3`: the `create-kubernetes-object` pipeline, its tasks, and the service accounts that run them.
   - `mlops/argocd/data-science-onboarding`: one `ObjectBucketClaim` per bucket, one PostSync Job per bucket, and the `dspa` pipeline server.
3. Each Job starts a PipelineRun. The pipeline waits until OpenShift Data Foundation publishes the claim Secret and ConfigMap, then writes the OpenShift AI connection Secret. Each name in `workbenchName` receives that connection on the same run.
4. `researcher-project` holds the workbench notebooks and the training pipeline that use those connections.

`mlops/argocd/ocp/application.yaml` is the Application in `openshift-gitops` that tracks `mlops/argocd/ocp`. The model registry objects land in `rhoai-model-registries`.

## Layout

| Path | Role |
| --- | --- |
| `mlops/argocd/ocp/setup` | Project, project Argo CD, model registry, and the onboarding Application |
| `mlops/argocd/data-science-onboarding` | Buckets, connection Jobs, and the pipeline server |
| `mlops/tekton/s3` | Pipeline, tasks, and service accounts |
| `mlops/tekton/s3/run-examples` | Manual PipelineRun examples |
| `researcher-project/notebooks` | Experiment, save, and request notebooks |
| `researcher-project/pipelines` | Kubeflow training pipeline |

## Add a bucket

List it under `buckets` in `mlops/argocd/data-science-onboarding/values.yaml`. Each entry needs a DNS-1123 `name`. The claim and the S3 bucket are named `<namespace>-<name>`. The next sync creates the claim and the Job `start-connection-<name>`.

Leave `connectionName` empty to use `aws-connection-<obc-name>`. Leave `region` empty to let the pipeline use `us-east-1` when the claim ConfigMap has no `BUCKET_REGION`. Leave `workbenchName` empty to publish the Secret without attaching it. Add one list entry per workbench that should receive the connection.

The pipeline server stores artifacts in `<namespace>-pipelines` and reads credentials from `aws-connection-pipelines`. Its NooBaa endpoint is `objectStorage` in the same values file.

## Requirements

- Red Hat OpenShift
- Red Hat OpenShift AI
- OpenShift Data Foundation, with the storage class set in `values.yaml` (`openshift-storage.noobaa.io` by default)
- OpenShift Pipelines
- OpenShift GitOps

## Author

Asier Cidon @RedHat
