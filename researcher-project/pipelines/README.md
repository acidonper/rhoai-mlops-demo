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
| `evaluate_keras_model_performance` | `evaluate_model.py` | Scores the full test set, logs that result on the Kubeflow MLflow run, traces the first 200 test rows, compares those traces with the previous evaluation, and fails at or below `0.01`. |
| `validate_onnx_model` | `evaluate_model.py` | Asserts ONNX and Keras predictions match. |
| `push_to_model_registry` | `save_model.py` | Stores the artifacts, registers `jukebox` as ONNX format version `1`, and logs that ONNX file on the same MLflow run. |

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

`evaluate_keras_model_performance` and `push_to_model_registry` receive these variables on their pods:

| Variable | Value |
| --- | --- |
| `MLFLOW_TRACKING_URI` | `https://mlflow.redhat-ods-applications.svc:8443/mlflow` |
| `MLFLOW_TRACKING_AUTH` | `kubernetes-namespaced` |
| `MLFLOW_K8S_INTEGRATION` | `true` |
| `MLFLOW_TRACKING_INSECURE_TLS` | `false` |

The Tekton task `execute-ds-pipeline` exports the same variables. Submitting the pipeline reads them and copies them onto those two pods. `REQUESTS_CA_BUNDLE` stays on the service CA, so the client verifies the tracking server certificate. A workbench submit uses the same defaults when those variables are unset.

The evaluation step writes to the MLflow run that the pipeline server creates for this Kubeflow run. It finds that run by the tag `kfp.pipeline_run_id`, using the pod label `pipeline/runid`. The workspace is the pod namespace (`MLFLOW_WORKSPACE`).

On that run it records:

- parameters for the model, version, namespace, cluster domain, Kubeflow run id, test size, traced size, and each training hyperparameter
- metrics for accuracy, weighted precision, recall, and F1 on the full test set, plus the previous registry accuracy
- a confusion-matrix table and a predictions table
- a trace for each of the first 200 test rows, scored by `label_match` (predicted country equals the label) and `confidence` (highest class probability)

When an earlier pipeline evaluation of the same model exists, the step calls `mlflow.genai.compare_evaluations` with `log_results=True`. That pairs the traces and logs `compare/<baseline>/<scorer>/{diff,ci_low,ci_high,p_value,effect_size,n_paired}` on the new run, plus a comparison artifact. The first evaluation has no baseline, and a comparison that is not significant does not fail the pipeline. Accuracy still fails the step at or below `0.01`.

The register step resumes the same run, logs dataset metadata, and logs the ONNX file as a new MLflow model version. That version carries the run metrics, which is what the Model metrics tab shows. The step leaves a Kubeflow-owned run running so the pipeline server can finish it. Open the pipeline run under **Develop & train > Experiments (MLflow)** to see the parameters, metrics, traces, and artifacts.

With `prod_flag` true, the logged model is tagged `prod=true` and the MLflow alias `prod` moves to the new registered version. The Kubeflow model registry metadata for the version includes `mlflow_run_id` and `mlflow_model_id`.

## Submit a run

Run this inside the project, from a workbench whose service account can reach `https://ds-pipeline-dspa.<namespace>.svc:8443`. The `__main__` block reads the pod namespace and service-account token.

Set `cluster_domain` in the `metadata` dict (the apps domain, such as `apps.example.com`). The other lab arguments are model name `jukebox`, version `0.0.2`, PVC `jukebox-model-pvc`, `prod_flag` `False`, and `epochs` `2`.

```bash
python prod_train_save_pipeline.py
```

The run is created in the experiment `kfp-training-pipeline` with caching enabled.

Upload the two parquet files to the models bucket before the first run. Local copies are in [`../datasets`](../datasets). The fetch test in [`tests/README.md`](tests/README.md) uses the same objects and the same `*_MODEL` variables.
