# Researcher project

Workbench notebooks and the Kubeflow pipeline for the jukebox model: a Keras network that predicts the country where a song is popular, exported to ONNX and registered in the project model registry.

## Layout

| Path | Role |
| --- | --- |
| [`notebooks`](notebooks/README.md) | Train a model in the workbench, register it, and send an inference request |
| [`pipelines`](pipelines/README.md) | Same training flow as a Kubeflow pipeline on the project pipeline server |
| [`pipelines/tests`](pipelines/tests/README.md) | Integration test for the fetch component |
| `datasets/` | `song_properties.parquet` and `song_rankings.parquet` to upload into the models bucket |
| `argocd/workbench.yaml` | Sample `Notebook` `test-workbench` in `project01` |
| `argocd/inferenceservice.yaml` | Sample `InferenceService` `jukebox` for the registered ONNX model |

## Before the notebooks

1. Finish [the platform setup](../README.md) so `project01`, `aws-connection-models`, `aws-connection-pipelines`, and `project01-registry` exist.
2. Upload `datasets/song_properties.parquet` and `datasets/song_rankings.parquet` to the keys `datasets/song_properties.parquet` and `datasets/song_rankings.parquet` in the models bucket. The training pipeline downloads those keys. The first notebook loads the same files from GitHub.
3. Review `argocd/workbench.yaml` and apply it, or create `test-workbench` from the dashboard. The sample mounts `aws-connection-models` with `envFrom` and sets `opendatahub.io/connections` to `project01/aws-connection-models`. It was exported from a lab cluster: confirm the namespace, image, and hardware profile before applying.

`argocd/inferenceservice.yaml` is the serving object for notebook 3. It was exported from the same lab. It expects an ONNX model at storage path `models/jukebox`, a serving runtime named `jukebox`, and model-registry labels for `project01-registry`.

## Data Scientist Step

### Try notebooks manually 

This phase aims to train and build an AI model leveraging a dedicated DEV workbench pipeline within Jupyter notebooks.

Follow [notebooks/README.md](notebooks/README.md), then submit the pipeline described in [pipelines/README.md](pipelines/README.md). 

## Datascience Workflow

This phase centers on establishing an automated framework for model training, building, and deployment. Pipelines and GitOps serve as critical pillars, and the objective is to deploy and configure both tooling components.

Please execute the following actions:

- Clone the origin model image from quay

```$bash
oc import-image jukebox:latest \
  --from=quay.io/rhoai-mlops/jukebox:latest \
  --confirm \ 
  -n project01
```

- Specify the target domain inside the `researcher-project/mlops/ops/values.yaml` file.
- Commit and push these updates to your remote repository.

```$bash
git push
```

- Provision the corresponding ArgoCD Application objects to spin up all required pipelines and infrastructure resources.

```$bash
oc apply -f researcher-project/mlops/argocd/application-ml.yaml
oc apply -f researcher-project/mlops/argocd/application-ops.yaml
```

- After reviewing both Application are synced in ArgoCD, execute the following emulation

```$bash
curl -sk -X POST \
  "https://el-ct-listener-project01.apps.ocp.b5frx.sandbox1967.opentlc.com" \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: $(uuidgen)" \
  -H "User-Agent: GitHub-Hookshot/curl" \
  -d '{
    "ref": "refs/heads/master",
    "head_commit": {
      "id": "47d6d1b608ce04927c5d732952ea1d668ec07371"
    },
    "repository": {
      "name": "rhoai-mlops-demo",
      "clone_url": "https://github.com/acidonper/rhoai-mlops-demo.git"
    },
    "pusher": {
      "username": "acidonper"
    }
  }'
```

NOTE: Update `head_commit`, `clone_url`and `TektonListenerURL`

## Author

Asier Cidon @RedHat