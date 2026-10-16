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

## Workbench order

Follow [notebooks/README.md](notebooks/README.md), then submit the pipeline described in [pipelines/README.md](pipelines/README.md).
