---
name: kfp-training-pipeline
description: >-
  Implements Kubeflow Pipelines (KFP) the way the RHOAI researcher training
  pipeline does: one module per stage, @component functions, artifact files,
  pipeline arguments, secret and namespace variables, and a workbench submit
  block. Use when the user asks to add or change a KFP or Kubeflow pipeline,
  define a component, wire pipeline variables, mount a data connection or
  PVC, or register a model from a pipeline.
---

# KFP training pipeline

Match `rhoai-mlops-demo/researcher-project/pipelines`. Client packages are `kfp==2.9.0` and `kfp-kubernetes==1.3.0`. Compile and submit from a workbench pod whose service account can reach `https://ds-pipeline-dspa.<namespace>.svc:8443`.

## Layout

Keep the pipeline directory flat. One stage per module. Two functions may share a module when they are the same stage (train and convert, evaluate and check ONNX).

| File | Role |
| --- | --- |
| `<stage>.py` | `@component` functions |
| `<name>_pipeline.py` | `@dsl.pipeline`, Kubernetes settings, `__main__` submit |
| `default_parameters.json` | Arguments that are not injected at submit time |
| `tests/test_<component>.py` | `kfp.local` subprocess run |
| `tests/requirements.txt` | `kfp==2.9.0`, `kfp-kubernetes==1.3.0`, and test extras |
| `pytest.ini` | `filterwarnings = ignore::DeprecationWarning` |

The pipeline module imports component functions by name. A component function must not import a sibling module. KFP ships only that function body, so runtime imports are installed packages inside the function.

## Component

```python
from kfp.dsl import component, Input, Output, Dataset, Metrics, Artifact, ClassificationMetrics

@component(
    base_image="tensorflow/tensorflow:2.21.0",
    packages_to_install=["numpy<2", "pandas==2.2.3"],
)
def preprocess_data(
    in_data: Input[Dataset],
    train_data: Output[Dataset],
    scaler: Output[Artifact],
):
    import pandas as pd

    df = pd.read_csv(in_data.path)
    train_data.path += ".pkl"
    scaler.path += ".pkl"
```

- Pin `base_image` and every `packages_to_install` entry. Use `python:3.9` for S3 fetch, `python:3.12` for registry upload, and `tensorflow/tensorflow:2.21.0` for Keras, preprocess, convert, and evaluate.
- Put pandas, boto3, keras, pickle, and registry imports inside the function. Keep `kfp` imports at module level for the decorator and annotations.
- Declare files as `Input` / `Output` of `Dataset`, `Artifact`, `Metrics`, or `ClassificationMetrics`. Declare run settings as `str`, `bool`, or `dict` (`hyperparameters` is a `dict`).
- KFP artifact paths have no suffix. Append one before writing, and read that same path downstream: `.csv`, `.pkl`, `.keras`, `.onnx`, `.txt`.
- Store source info on `dataset.metadata`. Log numbers with `metrics.log_metric("Accuracy", float(accuracy))` and a matrix with `classification_metrics.log_confusion_matrix(targets, matrix)`.
- Fail the step by raising `Exception`. `validate_data` returns `bool`, and the pipeline never reads that return. The raise is what stops the run.

Read secrets only from the environment:

```python
from os import environ

s3_endpoint_url = environ.get("AWS_S3_ENDPOINT_MODEL")
s3_access_key = environ.get("AWS_ACCESS_KEY_ID_MODEL")
s3_secret_key = environ.get("AWS_SECRET_ACCESS_KEY_MODEL")
s3_bucket_name = environ.get("AWS_S3_BUCKET_MODEL")
s3_region = environ.get("AWS_DEFAULT_REGION_MODEL")
```

Build the S3 client with `endpoint_url` and `verify=False`. The models connection uses the `_MODEL` suffix. The pipelines connection uses `AWS_S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, and `AWS_DEFAULT_REGION` with no suffix.

## Pipeline

```python
import kfp.dsl as dsl
from kfp import kubernetes
from data_preprocessing import preprocess_data

data_connection_secret_name_models = "aws-connection-models"
data_connection_secret_name_pipelines = "aws-connection-pipelines"

@dsl.pipeline(name="kfp-training-pipeline", description="We train an amazing model 🚂")
def training_pipeline(
    hyperparameters: dict,
    model_name: str,
    version: str,
    cluster_domain: str,
    model_storage_pvc: str,
    prod_flag: bool,
):
    fetch_task = fetch_data()  # imported from fetch_data.py
    kubernetes.use_secret_as_env(
        fetch_task,
        secret_name=data_connection_secret_name_models,
        secret_key_to_env={
            "AWS_S3_ENDPOINT": "AWS_S3_ENDPOINT_MODEL",
            "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID_MODEL",
            "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY_MODEL",
            "AWS_S3_BUCKET": "AWS_S3_BUCKET_MODEL",
            "AWS_DEFAULT_REGION": "AWS_DEFAULT_REGION_MODEL",
        },
    )
    pre_processing_task = preprocess_data(in_data=fetch_task.outputs["dataset"])
    pre_processing_task.after(data_validation_task)
```

- Pass an upstream file as `task.outputs["<parameter name>"]`. The key is the component parameter name.
- An artifact input already waits for the producer. Call `.after(task)` when this step must wait for a task whose output it does not take (validation before preprocess, ONNX check before register).
- Pass `version` into any cached step that must rerun for a new model version.
- On every task set both `AWS_CA_BUNDLE` and `REQUESTS_CA_BUNDLE` to `/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt`.
- Map `aws-connection-models` only onto the fetch task, with the `_MODEL` env names. Map `aws-connection-pipelines` only onto the register task, with the unsuffixed env names.
- On a task that reads `NAMESPACE` from the environment, add `kubernetes.use_field_path_as_env(task, env_name="NAMESPACE", field_path="metadata.namespace")`. The register step reads `/var/run/secrets/kubernetes.io/serviceaccount/namespace` instead, so it does not need that field path.
- `prod_flag` selects storage. `False` uploads the ONNX model, scaler, and label encoder through the pipelines connection and registers that S3 URI. `True` copies the ONNX model, Keras model, scaler, label encoder, and frozen requirements onto the PVC and registers the URI `to-be-updated`.
- Mount the PVC on the register task. The argument exists for this mount; `/models` is empty without it.

```python
kubernetes.mount_pvc(
    register_model_task,
    pvc_name=model_storage_pvc,
    mount_path="/models",
)
```

`model_storage_pvc` is a pipeline argument. `prod_train_save_pipeline.py` accepts it and does not call `mount_pvc`. Add the call when that register step writes under `/models`.

## Registry namespace

Take the first `-` segment of the pod namespace. With `prod_flag` true, append `-prod`. The registry host is `https://<namespace>-registry-rest.<cluster_domain>` on port 443 with `is_secure=False`. Before constructing `ModelRegistry`, set `KF_PIPELINES_SA_TOKEN_PATH` to `/var/run/secrets/kubernetes.io/serviceaccount/token`.

Register with `model_format_name="onnx"` and `model_format_version="1"`. Copy `metrics.metadata["Accuracy"]` into version metadata. Copy dataset metadata except `display_name` and `store_session_info`, and stringify every value.

## Submit

`default_parameters.json` holds only values the caller does not overwrite. In this pipeline that is `hyperparameters`. The Tekton task loads that file, then sets `version`, `model_name`, `model_storage_pvc`, `cluster_domain`, and `prod_flag`. Keys of the arguments dict must match the pipeline function parameters.

The workbench `__main__` block may pass a full metadata dict instead of the file. It reads the namespace file and the service-account token, then:

```python
client = kfp.Client(
    host=f"https://ds-pipeline-dspa.{namespace}.svc:8443",
    existing_token=bearer_token,
    ssl_ca_cert="/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt",
)
client.create_run_from_pipeline_func(
    training_pipeline,
    arguments=metadata,
    experiment_name="kfp-training-pipeline",
    enable_caching=True,
)
```

Leave `cluster_domain` for the caller to set. Do not invent an apps domain.

## Test a component

Run from the pipeline directory with `PYTHONPATH` set to that directory. Initialize `kfp.local` with `SubprocessRunner()`, call the component, and read `task.outputs["<name>"].path`. Delete `local_outputs` in an autouse fixture. Export the same env names the task injects before a test that reaches S3. Do not mock that download when the existing fetch test hits the real bucket objects.

## Checklist

- [ ] Runtime imports sit inside the component function, and third-party packages are pinned.
- [ ] Each output path gets its suffix before the file is written.
- [ ] Secret env names match the connection: `_MODEL` for models, unsuffixed for pipelines.
- [ ] Every task sets both CA bundle variables.
- [ ] A step with no artifact edge uses `.after`.
- [ ] `version` reaches steps that must bypass the cache.
- [ ] Registry namespace is the first namespace segment, plus `-prod` when `prod_flag` is true.
- [ ] The register task mounts `model_storage_pvc` at `/models` when it copies artifacts there.
- [ ] `default_parameters.json` and the pipeline signature stay in sync with the submit arguments.
