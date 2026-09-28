# AI/ML Lifecycle with Red Hat OpenShift AI

Demo of a GitOps path that creates OpenShift Data Foundation buckets and publishes them as Red Hat OpenShift AI S3 data connections.

OpenShift GitOps syncs one Application with two sources into the `project01` namespace:

1. Tekton tasks, the `create-kubernetes-object` pipeline, and RBAC from `mlops/tekton/s3`.
2. The `project01` Helm chart from `mlops/argocd/project01`.

The chart creates the project namespace, one `ObjectBucketClaim` per bucket, and one PostSync Job per bucket. Each Job starts a PipelineRun. The pipeline waits until ODF publishes the bucket Secret and ConfigMap, then creates the OpenShift AI connection Secret. Each name in `workbenchName` receives that connection in the same PipelineRun.

## Layout

| Path | Role |
| --- | --- |
| `mlops/argocd/application.yaml` | Argo CD Application that syncs both sources |
| `mlops/argocd/project01/` | Helm chart: namespace, buckets, and one Job per bucket |
| `mlops/tekton/s3/` | Pipeline, tasks, and service accounts |
| `mlops/tekton/s3/run-examples/` | Manual PipelineRun examples |

## Key Scenarios

### Provisioning environment workbenches with direct S3 integration

Overall sequence:

1. Initialize an Object Storage claim within ODF using automated GitOps workflows
2. Trigger a dedicated Kubernetes Job during the post-synchronization step:
2.1 Establish an S3 connection in OpenShift AI, generating the target bucket secret via automated pipelines
2.2 Bind the active notebook workspace to S3 credentials using metadata annotations

#### Add a bucket

List it under `buckets` in `mlops/argocd/project01/values.yaml`. Each entry needs a DNS-1123 `name`. The next sync creates the claim `ObjectBucketClaim` and the Job `start-connection-<name>`.

Leave `connectionName` empty to use `aws-connection-<name>`. Leave `region` empty to use the chart `region`. Leave `workbenchName` empty to publish the Secret without attaching it. Add one list entry per workbench that should receive the connection.

## Requirements

- Red Hat OpenShift
- Red Hat OpenShift AI
- OpenShift Data Foundation, with the storage class set in `values.yaml` (`openshift-storage.noobaa.io` by default)
- OpenShift Pipelines
- OpenShift GitOps

## Author

Asier Cidon @RedHat
