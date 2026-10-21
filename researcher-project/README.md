# Researcher project

Workbench notebooks and the Kubeflow pipeline for the jukebox model: a Keras network that predicts the country where a song is popular, exported to ONNX and registered in the project model registry.

## Before the notebooks

1. Finish [the platform setup](../README.md) so `project01`, `aws-connection-models`, `aws-connection-pipelines`, and `project01-registry` exist.
2. Upload `datasets/song_properties.parquet` and `datasets/song_rankings.parquet` to the keys `datasets/song_properties.parquet` and `datasets/song_rankings.parquet` in the models bucket. The training pipeline downloads those keys. The first notebook loads the same files from GitHub.
3. Create a new workbench, `test-workbench`, from the RHOAI dashboard configuring:
- Notebook Image: Jupyter | Data Science | CPU | Python 3.12 (Version 2025.2)
- Deployment size: Memory requests -> 6 GiB / Memory limits -> 8 GiB
- Connections: Select `aws-connection-models`

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

- Upon successful execution of the Tekton pipeline, proceed with deploying the application to leverage the newly generated model. Ensure you retrieve the target commit tag ID via RHOAI Dashboard -> Models -> Registry -> jukebox -> Select latest version (e.g., `6462d76b18`).

- Next, promote this model artifact to production by updating the `researcher-project/mlops/ml/values.yaml` file, specifying the target `version` and verifying the corresponding `model_endpoint` configuration.

- To conclude, commit and push your updates to Git to trigger automated deployment through ArgoCD.

NOTE: Update `head_commit`, `clone_url`and `TektonListenerURL`

## Author

Asier Cidon @RedHat