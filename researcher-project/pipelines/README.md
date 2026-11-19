# Training pipeline

Kubeflow pipeline `kfp-training-pipeline` in [`prod_train_save_pipeline.py`](prod_train_save_pipeline.py). It repeats the notebook flow on the project pipeline server (`dspa`): fetch the jukebox tables, validate them, preprocess, train, convert to ONNX, evaluate, check that ONNX matches Keras, and register the model.

## Steps

| Step | Module | What it does |
| --- | --- | --- |
| `fetch_data` | `fetch_data.py` | Downloads `datasets/song_properties.parquet` and `datasets/song_rankings.parquet`, merges them on `spotify_id`, and writes a CSV dataset. |
| `validate_data` | `data_validation.py` | Fails when the dataset path is missing. |
| `preprocess_data` | `data_preprocessing.py` | Drops empty rows, splits train, validation, and test, and writes the scaler and label encoder. |
| `train_model` | `train_model.py` | Trains the Keras network and records `pip freeze` output. |
| `convert_keras_to_onnx` | `train_model.py` | Converts the trained model to ONNX. |
| `evaluate_keras_model_performance` | `evaluate_model.py` | Scores the full test set and fails at or below `0.01`. |
| `validate_onnx_model` | `evaluate_model.py` | Asserts ONNX and Keras predictions match. |
| `push_to_model_registry` | `save_model.py` | Stores the artifacts, registers `jukebox` as ONNX format version `1`, and registers that ONNX file as the next MLflow model version. |

## Connections

`fetch_data` reads the models connection. The pipeline mounts `aws-connection-models` with these environment names:

| Secret key | Variable in the component |
| --- | --- |
| `AWS_S3_ENDPOINT` | `AWS_S3_ENDPOINT_MODEL` |
| `AWS_ACCESS_KEY_ID` | `AWS_ACCESS_KEY_ID_MODEL` |
| `AWS_SECRET_ACCESS_KEY` | `AWS_SECRET_ACCESS_KEY_MODEL` |
| `AWS_S3_BUCKET` | `AWS_S3_BUCKET_MODEL` |
| `AWS_DEFAULT_REGION` | `AWS_DEFAULT_REGION_MODEL` |

`push_to_model_registry` reads `aws-connection-pipelines` as `AWS_S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, and `AWS_DEFAULT_REGION`.

The registration step always mounts `model_storage_pvc` at `/models`. `prod_flag` selects where the artifacts are stored:

- `false`: upload the ONNX model, scaler, and label encoder to the pipelines bucket and register that S3 URI. Notebook 2 uploads to the models bucket; this path uses the pipelines connection.
- `true`: copy the ONNX model, Keras model, scaler, label encoder, and frozen requirements onto that PVC, and register the URI `to-be-updated`.

The registry address is `https://<namespace>-registry-rest.<cluster_domain>`. `<namespace>` is the first segment of the pod namespace. With `prod_flag` true, that segment gains a `-prod` suffix, so a run in `project01` talks to `project01-prod-registry`.

## MLflow

Only `push_to_model_registry` talks to MLflow. It registers the ONNX file as a new version of the model. The evaluation step does not write runs, traces, or metrics.

The register pod receives these variables:

| Variable | Value |
| --- | --- |
| `MLFLOW_TRACKING_URI` | `https://mlflow.redhat-ods-applications.svc:8443/mlflow` |
| `MLFLOW_TRACKING_AUTH` | `kubernetes-namespaced` |
| `MLFLOW_K8S_INTEGRATION` | `true` |
| `MLFLOW_TRACKING_INSECURE_TLS` | `false` |

The Tekton task `execute-ds-pipeline` exports the same variables. Submitting the pipeline reads them and copies them onto the register pod. `REQUESTS_CA_BUNDLE` stays on the service CA, so the client verifies the tracking server certificate. A workbench submit uses the same defaults when those variables are unset. The workspace is the pod namespace (`MLFLOW_WORKSPACE`).

Registration creates the next version of the registered model named after `model_name`:

- the ONNX file is the version artifact
- accuracy, weighted precision, recall, and F1 are linked to that version
- the version description records the pipeline version, accuracy, and weighted F1
- tags `pipeline_version` and `accuracy` are set on the version

Open the model under **Develop & train > Model registry (MLflow)** and compare versions by those metrics. The version tag `prod` is `true` or `false`. With `prod_flag` true, the alias `prod` moves to the new version. The Kubeflow model registry metadata for the version includes `mlflow_model_id` and `mlflow_registered_version`. Accuracy still fails the evaluation step at or below `0.01`.

## Submit a run

Run this inside the project, from a workbench whose service account can reach `https://ds-pipeline-dspa.<namespace>.svc:8443`. The `__main__` block reads the pod namespace and service-account token.

Set `cluster_domain` in the `metadata` dict (the apps domain, such as `apps.example.com`). The other lab arguments are model name `jukebox`, version `0.0.2`, PVC `jukebox-model-pvc`, `prod_flag` `False`, and `epochs` `2`.

```bash
python prod_train_save_pipeline.py
```

The run is created in the experiment `kfp-training-pipeline` with caching enabled.

Upload the two parquet files to the models bucket before the first run. Local copies are in [`../datasets`](../datasets). The fetch test in [`tests/README.md`](tests/README.md) uses the same objects and the same `*_MODEL` variables.
