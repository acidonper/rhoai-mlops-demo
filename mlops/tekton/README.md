# OpenShift Pipelines

Tekton pipelines synced into the data science project by Application `data-science-onboarding`.

The Application source is the `s3` directory. YAML nested in `s3/run-examples/` is left for manual `oc create`.

## create-kubernetes-object

Pipeline that creates one Kubernetes object, publishes an OpenShift AI S3 connection from an OpenShift Data Foundation `ObjectBucketClaim`, or does both. Application `data-science-onboarding` syncs the YAML in this directory into the project namespace. The onboarding chart's PostSync Jobs are the usual caller; see [../../helm/data-science-onboarding/README.md](../../helm/data-science-onboarding/README.md).

### Files

| File | Role |
| --- | --- |
| `pipeline.yaml` | Pipeline `create-kubernetes-object` |
| `task-apply-kubernetes-object.yaml` | Task `apply-kubernetes-object`: `oc apply` of a single manifest |
| `task-create-rhoai-data-connection.yaml` | Task `create-rhoai-data-connection`: wait for the claim, write the connection Secret, annotate Notebooks |
| `rbac.yaml` | Service accounts, Roles, and RoleBindings used by the pipeline and by the PostSync Job |
| `run-examples/` | PipelineRuns to create by hand |

`apply-object` runs when `manifest` is non-empty. `create-rhoai-connection` runs after it when `obc-name` is non-empty. With an empty manifest, only the connection task runs.

### Service accounts

| Name | Used by | Can |
| --- | --- | --- |
| `pipeline-object-creator` | PipelineRun task pods | `get`, `list`, `create`, `update`, and `patch` ConfigMaps, Secrets, and ObjectBucketClaims; `get`, `patch`, and `update` Notebooks |
| `pipeline-run-creator` | PostSync Job | `create` PipelineRuns |

The apply task only succeeds for objects this Role allows. The sample manifest in `run-examples/example-pipelinerun.yaml` is a ConfigMap and an ObjectBucketClaim.

### Parameters

| Parameter | Default | Effect |
| --- | --- | --- |
| `manifest` | empty | YAML of one object. Empty skips `apply-object`. |
| `namespace` | empty | Target namespace. Empty uses the run namespace. |
| `obc-name` | empty | ObjectBucketClaim whose Secret and ConfigMap supply the credentials. Empty skips the connection task. |
| `connection-name` | empty | Connection Secret name. Empty uses `aws-connection-<obc-name>`. |
| `connection-display-name` | empty | `openshift.io/display-name`. Empty uses the Secret name. |
| `workbench-names` | `[]` | Notebooks that receive the connection. Empty publishes the Secret only. |
| `region` | `us-east-1` | Used when the claim ConfigMap has no `BUCKET_REGION`. An empty value also falls back to `us-east-1` inside the task. |

The connection Secret is `Opaque` and labeled for the OpenShift AI dashboard (`opendatahub.io/dashboard`, `opendatahub.io/managed`, connection type `s3`). `stringData` contains `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_ENDPOINT`, `AWS_S3_BUCKET`, and `AWS_DEFAULT_REGION`. The endpoint is `https://<BUCKET_HOST>` plus `BUCKET_PORT` when the host has no port yet.

For each workbench, the task sets `opendatahub.io/connections` to `<namespace>/<connection-name>`, keeping connection refs already on the annotation. The Notebook must already exist.

The task polls the claim Secret and ConfigMap for up to 60 attempts, five seconds apart.

### Run an example

The GitOps sync already applies `rbac.yaml`, both tasks, and `pipeline.yaml`. To start a sample run in `project01`:

```bash
oc create -n project01 -f mlops/tekton/s3/run-examples/example-rhoai-connection-pipelinerun.yaml
```

`example-rhoai-connection-pipelinerun.yaml` waits for an ObjectBucketClaim named `example-obc` and writes `aws-connection-example-obc`. `example-pipelinerun.yaml` applies a ConfigMap and an ObjectBucketClaim named `example-from-pipeline`. Edit `obc-name`, `connection-name`, and `workbench-names` before creating a run against a real bucket.

To install the pipeline without the Application:

```bash
oc apply -n project01 \
  -f mlops/tekton/s3/rbac.yaml \
  -f mlops/tekton/s3/task-apply-kubernetes-object.yaml \
  -f mlops/tekton/s3/task-create-rhoai-data-connection.yaml \
  -f mlops/tekton/s3/pipeline.yaml
```
