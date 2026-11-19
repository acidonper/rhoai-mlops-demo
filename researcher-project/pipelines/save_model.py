import kfp
import kfp.dsl as dsl
from kfp.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Metrics,
    Artifact,
)

@component(base_image='python:3.12', packages_to_install=['pip==25.3', 'setuptools==80.9.0', 'boto3==1.40.76', 'model-registry==0.3.7', 'mlflow[kubernetes]==3.18.0', 'onnx==1.20.1', 'protobuf==7.34.0', 'pandas==2.2.3'])

def push_to_model_registry(
    model_name: str,
    version: str,
    cluster_domain: str,
    prod_flag: bool,
    hyperparameters: dict,
    keras_model: Input[Artifact],
    model: Input[Artifact],
    metrics: Input[Metrics],
    scaler: Input[Artifact],
    label_encoder: Input[Artifact],
    dataset: Input[Dataset],
    training_dependencies: Input[Artifact],
):
    from os import environ, path, makedirs
    from datetime import datetime
    from model_registry import ModelRegistry, utils
    import shutil
    import json
    from boto3 import client
    
    if prod_flag:
        ############ Save to PVC ############
        makedirs("/models/artifacts", exist_ok=True)
        shutil.copyfile(model.path, f"/models/{model_name}.onnx")
        shutil.copyfile(keras_model.path, f"/models/{model_name}.keras")
        shutil.copyfile(scaler.path, f"/models/artifacts/scaler.pkl")
        shutil.copyfile(label_encoder.path, f"/models/artifacts/label_encoder.pkl")
        shutil.copyfile(training_dependencies.path, f"/models/artifacts/frozen_training_requirements.txt")
    else:
        ############ Upload to S3 ############
        model_object_prefix = model_name if model_name else "model"
        s3_endpoint_url = environ.get('AWS_S3_ENDPOINT')
        s3_access_key = environ.get('AWS_ACCESS_KEY_ID')
        s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY')
        s3_bucket_name = environ.get('AWS_S3_BUCKET')
        s3_region = environ.get('AWS_DEFAULT_REGION')
        version = version if version else datetime.now().strftime('%y%m%d%H%M')

        s3_client = client(
            "s3",
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            endpoint_url=s3_endpoint_url,
            region_name=s3_region,
            verify=False
        )

        def _generate_artifact_name(artifact_file_name, version=''):
            artifact_name, artifact_extension = path.splitext(path.basename(artifact_file_name))
            artifact_version_file_name = f'{artifact_name}-{version}{artifact_extension}'
            print(artifact_version_file_name)
            return artifact_version_file_name

        def _do_upload(s3_client, model_path, object_name, s3_bucket_name):
            print(f'Uploading model to {object_name}')
            try:
                s3_client.upload_file(model_path, s3_bucket_name, object_name)
            except Exception as e:
                print(f'S3 upload to bucket {s3_bucket_name} at {s3_endpoint_url} failed: {e}')
                raise
            print(f'Model uploaded and available as "{object_name}"')

        model_artifact_s3_path = f"/models/{model_name}/1/{_generate_artifact_name(f'{model_name}.onnx', version)}"
        scaler_artifact_s3_path = f"/models/{model_name}/1/artifacts/{_generate_artifact_name(scaler.path, version)}"
        label_encoder_artifact_s3_path = f"/models/{model_name}/1/artifacts/{_generate_artifact_name(label_encoder.path, version)}"

        _do_upload(s3_client, model.path, model_artifact_s3_path, s3_bucket_name)
        _do_upload(s3_client, scaler.path, scaler_artifact_s3_path, s3_bucket_name)
        _do_upload(s3_client, label_encoder.path, label_encoder_artifact_s3_path, s3_bucket_name)

    environ["KF_PIPELINES_SA_TOKEN_PATH"] = "/var/run/secrets/kubernetes.io/serviceaccount/token"

    ############ Register to Model Registry ############
    namespace_file_path =\
        '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_file_path, 'r') as namespace_file:
        pod_namespace = namespace_file.read().strip()

    # The MLflow workspace is the project namespace. Registration uses
    # kubernetes-namespaced auth. The model-registry host uses the first
    # segment, plus -prod when this run publishes a production model.
    environ["MLFLOW_WORKSPACE"] = pod_namespace

    if prod_flag:
        namespace = pod_namespace.split("-")[0]+"-prod"
    else:
        namespace = pod_namespace.split("-")[0]

    model_object_prefix = model_name if model_name else "model"
    version = version if version else datetime.now().strftime('%y%m%d%H%M')
    server_address = f"https://{namespace}-registry-rest.{cluster_domain}"

    registry = ModelRegistry(
        server_address=server_address,
        port=443,
        author=namespace,
        is_secure=False
    )
    registered_model_name = model_object_prefix

    # Log the ONNX file as an MLflow 3 LoggedModel. The model keeps its
    # training parameters, and the evaluation metrics are linked to that
    # model and to the song dataset so versions can be compared.
    import mlflow
    import onnx
    import pandas as pd
    from mlflow.entities import Dataset

    tracking_uri = environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise Exception("MLFLOW_TRACKING_URI is not set")
    environ.setdefault("MLFLOW_TRACKING_AUTH", "kubernetes-namespaced")
    environ.setdefault("MLFLOW_K8S_INTEGRATION", "true")
    environ.setdefault("MLFLOW_TRACKING_INSECURE_TLS", "false")
    environ.pop("MLFLOW_RUN_ID", None)
    environ.pop("MLFLOW_EXPERIMENT_ID", None)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name=registered_model_name)

    feature_columns = [
        "is_explicit", "duration_ms", "danceability", "energy", "key",
        "loudness", "mode", "speechiness", "acousticness", "instrumentalness",
        "liveness", "valence", "tempo",
    ]
    song_df = pd.read_csv(dataset.path)
    with open(scaler.path, "rb") as scaler_file:
        scaler_ = pd.read_pickle(scaler_file)
    sample = song_df[feature_columns].dropna().head(2)
    scaled_sample = pd.DataFrame(
        scaler_.transform(sample),
        columns=feature_columns,
    ).astype("float32")
    input_example = {
        name: scaled_sample[[name]].to_numpy() for name in feature_columns
    }
    model_params = {"version": version, "prod": str(prod_flag).lower()}
    for key, value in hyperparameters.items():
        if isinstance(value, (int, float, str, bool)):
            model_params[str(key)] = value
        else:
            model_params[str(key)] = str(value)

    onnx_model = onnx.load(model.path)
    with mlflow.start_run(run_name=version):
        logged_dataset: Dataset = mlflow.data.from_pandas(song_df, name=registered_model_name)
        model_info = mlflow.onnx.log_model(
            onnx_model,
            name=registered_model_name,
            params=model_params,
            input_example=input_example,
        )
        logged_model = mlflow.get_logged_model(model_info.model_id)
        print(logged_model.model_id, logged_model.params)

        mlflow.log_metrics(
            metrics={
                "accuracy": float(metrics.metadata["Accuracy"]),
                "weighted_precision": float(metrics.metadata["Weighted Precision"]),
                "weighted_recall": float(metrics.metadata["Weighted Recall"]),
                "weighted_f1": float(metrics.metadata["Weighted F1"]),
            },
            model_id=logged_model.model_id,
            dataset=logged_dataset,
        )
        logged_model = mlflow.get_logged_model(model_info.model_id)
        print(logged_model.model_id, logged_model.metrics)

    metadata = {
            "accuracy": str(metrics.metadata['Accuracy']),
        } | {key : str(value) for key, value in dataset.metadata.items() if key not in ["display_name", "store_session_info"]}
    metadata["mlflow_model_id"] = str(model_info.model_id) 

    if not prod_flag:
        s3_path_updated_format = utils.s3_uri_from(model_artifact_s3_path,
                                                   bucket=s3_bucket_name,
                                                   endpoint=s3_endpoint_url,
                                                   region=s3_region)

    registry.register_model(
        registered_model_name,
        "to-be-updated" if prod_flag else s3_path_updated_format,
        model_format_name="onnx",
        model_format_version="1",
        version=version,
        version_description=f"{registered_model_name} is a dense neural network. Built with Keras and it has 4 layers. It's been trained on a music dataset consisting of 14K songs and 1.1M data points where the songs are popular. To use send an array of 13 normalized values representing the song features to the input layer is called `input`. The output layer is called `outputs` and will return 72 values, each representing the probability that the song will be popular in that country.",
        metadata=metadata
    )
    print("Model registered successfully")