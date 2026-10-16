# AI/ML lifecycle with Red Hat OpenShift AI

This repository is a lab for an MLOps flow on Red Hat OpenShift AI. GitOps installs a data science project, a project-local Argo CD, a MySQL-backed model registry, S3 buckets, OpenShift AI data connections, and a pipeline server. From a workbench in that project you train the jukebox model, register it, and call it.

## Install

Log in with `oc` as a cluster admin. The cluster needs Red Hat OpenShift AI, OpenShift Data Foundation, and OpenShift Pipelines. `setup.sh` installs OpenShift GitOps and uses the default Argo CD instance in `openshift-gitops`.

```bash
cd mlops/ocp
./setup.sh
```

The script creates the `openshift-gitops-operator` and `project01` namespaces, subscribes to the GitOps operator, and applies two Applications. Names to change for another cluster are listed in [mlops/ocp/README.md](mlops/ocp/README.md).

## What the sync creates

`ocp-setup-project` renders [mlops/helm/setup-project](mlops/helm/setup-project). That chart installs an Argo CD instance in `project01` and the Application `data-science-onboarding`.

`data-science-onboarding` syncs two paths into `project01`:

- [mlops/tekton/s3](mlops/tekton/s3): the `create-kubernetes-object` pipeline, its tasks, and the service accounts that run them.
- [mlops/helm/data-science-onboarding](mlops/helm/data-science-onboarding): one `ObjectBucketClaim` per bucket, one PostSync Job per bucket, and the `dspa` pipeline server.

Each Job starts a PipelineRun. The run waits until OpenShift Data Foundation publishes the claim Secret and ConfigMap, writes the OpenShift AI connection Secret, and annotates every Notebook listed in `workbenchName` with that connection.

`ocp-setup-registry` renders [mlops/helm/setup-registry](mlops/helm/setup-registry) into `rhoai-model-registries`: MySQL and a `ModelRegistry` named `project01-registry`.

## Lab names

| Item | Value |
| --- | --- |
| Data science project | `project01` |
| Git revision | `master` on `https://github.com/acidonper/rhoai-mlops-demo.git` |
| Model registry namespace | `rhoai-model-registries` |
| Model registry | `project01-registry` |
| Workbenches | `test-workbench`, `test-workbench-1` |
| Buckets | `project01-models`, `project01-pipelines` |
| Connections | `aws-connection-models`, `aws-connection-pipelines` |

## Layout

| Path | Role |
| --- | --- |
| [`mlops/ocp`](mlops/ocp/README.md) | GitOps operator subscription and the two bootstrap Applications |
| [`mlops/helm/setup-project`](mlops/helm/setup-project/README.md) | Project Argo CD and the onboarding Application |
| [`mlops/helm/setup-registry`](mlops/helm/setup-registry/README.md) | Model registry and its MySQL database |
| [`mlops/helm/data-science-onboarding`](mlops/helm/data-science-onboarding/README.md) | Buckets, connection Jobs, and the pipeline server |
| [`mlops/tekton/s3`](mlops/tekton/s3/README.md) | Pipeline, tasks, and service accounts |
| `mlops/tekton/s3/run-examples` | PipelineRuns to create by hand |
| [`researcher-project`](researcher-project/README.md) | Notebooks, training pipeline, and sample workbench manifests |

## Add a bucket

Add an entry under `buckets` in [`mlops/helm/data-science-onboarding/values.yaml`](mlops/helm/data-science-onboarding/values.yaml). The next sync creates the claim `<namespace>-<name>` and the Job `start-connection-<name>`. Field rules are in the [chart README](mlops/helm/data-science-onboarding/README.md).

## Train and call the model

Apply the workbench yourself, then follow [researcher-project/README.md](researcher-project/README.md). The notebooks and the training pipeline expect `aws-connection-models`, `aws-connection-pipelines`, and `project01-registry` to exist.

## Requirements

- Red Hat OpenShift
- Red Hat OpenShift AI, with the model registry component so the `rhoai-model-registries` namespace exists
- OpenShift Data Foundation, with the storage class set in `values.yaml` (`openshift-storage.noobaa.io` by default)
- OpenShift Pipelines
- OpenShift GitOps

## Author

Asier Cidon @RedHat
