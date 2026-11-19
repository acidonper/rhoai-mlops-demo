import kfp
import kfp.dsl as dsl
from kfp.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Metrics,
    Artifact,
    ClassificationMetrics,
)

@component(base_image="tensorflow/tensorflow:2.21.0", packages_to_install=["numpy<2", "tf2onnx==1.17.0", "onnx==1.20.1", "pandas==2.2.3", "scikit-learn==1.6.1", "model-registry==0.3.7", "protobuf==7.34.0", "mlflow[kubernetes]==3.18.0"])
def evaluate_keras_model_performance(
    model: Input[Artifact],
    test_data: Input[Dataset],
    scaler: Input[Artifact],
    label_encoder: Input[Artifact],
    model_name: str,
    cluster_domain: str,
    version: str,
    prod_flag: bool,
    hyperparameters: dict,
    metrics: Output[Metrics],
    classification_metrics: Output[ClassificationMetrics]
):
    import keras
    import pandas as pd
    from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
    import numpy as np
    from os import environ
    from model_registry import ModelRegistry
    from model_registry.exceptions import StoreError
    
    trained_model = keras.saving.load_model(model.path)
    with open(test_data.path, 'rb') as pickle_file:
        X_test, y_test = pd.read_pickle(pickle_file)
    with open(scaler.path, 'rb') as pickle_file:
        scaler_ = pd.read_pickle(pickle_file)
    with open(label_encoder.path, 'rb') as pickle_file:
        label_encoder_ = pd.read_pickle(pickle_file)

    test_inputs = {name: X_test[[name]].to_numpy() for name in X_test.columns}
    y_pred_temp = trained_model.predict(test_inputs)
    y_pred_temp = np.asarray(np.squeeze(y_pred_temp))
    
    y_pred_argmax = np.argmax(y_pred_temp, axis=1)
    y_test_argmax = np.argmax(y_test, axis=1)
    
    accuracy = np.sum(y_pred_argmax == y_test_argmax) / len(y_pred_argmax)
    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        y_test_argmax,
        y_pred_argmax,
        average="weighted",
        zero_division=0,
    )
    
    # Get the previous models properties from the Model Registry
    if prod_flag:
        namespace = environ.get("NAMESPACE").split("-")[0]+"-prod"
    else:
        namespace = environ.get("NAMESPACE").split("-")[0]

    environ["KF_PIPELINES_SA_TOKEN_PATH"] = "/var/run/secrets/kubernetes.io/serviceaccount/token" # Hotfix to access the endpoint
    registry = ModelRegistry(server_address=f"https://{namespace}-registry-rest.{cluster_domain}", port=443, author="someone", is_secure=False)
    previous_model_properties = {}

    #Wrap with try except to see if the model exists in the registry
    try:
        # Get the latest models properties if no model is in production
        for v in registry.get_model_versions(model_name).order_by_id().descending():
            if not previous_model_properties:
                previous_model_properties = registry.get_model_versions(model_name).order_by_id().descending().next_item().custom_properties
            elif "prod" in v.custom_properties and v.custom_properties["prod"]:
                previous_model_properties = v.custom_properties
                break
    except StoreError:
        pass

    if "accuracy" not in previous_model_properties:
        previous_model_properties["accuracy"] = 0.1

    print("Previous model metrics: ", previous_model_properties)
    print("Accuracy: ", accuracy)

    # Log traces, pipeline context, and model metrics on the Kubeflow pipeline run.
    # The next run compares this evaluation with mlflow.genai.compare_evaluations.
    import mlflow
    from mlflow.genai.scorers import scorer

    tracking_uri = environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        raise Exception("MLFLOW_TRACKING_URI is not set")
    workspace = (environ.get("NAMESPACE") or "").strip()
    if not workspace:
        raise Exception("NAMESPACE is not set")
    environ["MLFLOW_WORKSPACE"] = workspace
    environ.setdefault("MLFLOW_TRACKING_AUTH", "kubernetes-namespaced")
    environ.setdefault("MLFLOW_K8S_INTEGRATION", "true")
    environ.setdefault("MLFLOW_TRACKING_INSECURE_TLS", "false")
    environ["MLFLOW_GENAI_EVAL_MAX_WORKERS"] = "4"
    injected_run_id = environ.pop("MLFLOW_RUN_ID", None)
    environ.pop("MLFLOW_EXPERIMENT_ID", None)
    mlflow.set_tracking_uri(tracking_uri)
    mlflow_client = mlflow.MlflowClient()

    def _experiment_ids():
        return [item.experiment_id for item in mlflow_client.search_experiments(max_results=1000)]

    kfp_run_id = (environ.get("KFP_PIPELINE_RUN_ID") or "").strip()
    parent_run = None
    if kfp_run_id:
        experiment_ids = _experiment_ids()
        if experiment_ids:
            matched = mlflow_client.search_runs(
                experiment_ids=experiment_ids,
                filter_string=f"tags.`kfp.pipeline_run_id` = '{kfp_run_id}'",
                max_results=50,
            )
            parents = [
                item for item in matched
                if "mlflow.parentRunId" not in (item.data.tags or {})
            ]
            if parents:
                parent_run = min(parents, key=lambda item: item.info.start_time)

    if parent_run is not None:
        print("MLflow pipeline run:", parent_run.info.run_id, parent_run.info.run_name)
        mlflow.start_run(run_id=parent_run.info.run_id)
        run_owner = "kfp"
    elif injected_run_id:
        mlflow.start_run(run_id=injected_run_id)
        run_owner = "kfp"
    else:
        experiment = mlflow.set_experiment(model_name)
        mlflow.start_run(experiment_id=experiment.experiment_id, run_name=version)
        run_owner = "pipeline"

    trace_limit = min(200, len(y_pred_argmax))
    labels = [str(label) for label in label_encoder_.classes_.tolist()]
    evaluation_rows = []
    prediction_rows = []
    for row_index in range(trace_limit):
        features = {
            column: float(X_test.iloc[row_index][column])
            for column in X_test.columns
        }
        expected_label = str(label_encoder_.inverse_transform([int(y_test_argmax[row_index])])[0])
        predicted_label = str(label_encoder_.inverse_transform([int(y_pred_argmax[row_index])])[0])
        confidence = float(np.max(y_pred_temp[row_index]))
        evaluation_rows.append({
            "inputs": {"features": features, "row_index": int(row_index)},
            "expectations": {"label": expected_label},
        })
        prediction_rows.append({
            "row_index": int(row_index),
            "expected_label": expected_label,
            "predicted_label": predicted_label,
            "confidence": confidence,
            "match": int(predicted_label == expected_label),
        })

    def predict_fn(features, row_index):
        index = int(row_index)
        probabilities = np.asarray(y_pred_temp[index], dtype=float)
        predicted_index = int(np.argmax(probabilities))
        return {
            "label": labels[predicted_index],
            "confidence": float(np.max(probabilities)),
        }

    @scorer
    def label_match(outputs, expectations) -> bool:
        return outputs["label"] == expectations["label"]

    @scorer
    def confidence(outputs) -> float:
        return float(outputs["confidence"])

    run_params = {
        "model_name": model_name,
        "version": version,
        "prod_flag": str(prod_flag).lower(),
        "namespace": workspace,
        "cluster_domain": cluster_domain,
        "kfp_pipeline_run_id": kfp_run_id,
        "test_samples": str(len(y_pred_argmax)),
        "traced_samples": str(trace_limit),
    }
    for key, value in hyperparameters.items():
        run_params[f"hp_{key}"] = str(value)[:500]

    try:
        existing_params = set(mlflow.active_run().data.params)
        new_params = {
            key: value for key, value in run_params.items() if key not in existing_params
        }
        if new_params:
            mlflow.log_params(new_params)
        mlflow.set_tags({
            "model_name": model_name,
            "version": version,
            "prod": str(prod_flag).lower(),
            "evaluation": "pipeline",
            "pipeline": "kfp-training-pipeline",
            "mlflow.note.content": (
                f"kfp-training-pipeline {version} evaluated {model_name}. "
                f"Accuracy {float(accuracy):.4f} on {len(y_pred_argmax)} test rows. "
                f"The first {trace_limit} rows are traced for comparison."
            ),
        })
        evaluation = mlflow.genai.evaluate(
            data=evaluation_rows,
            predict_fn=predict_fn,
            scorers=[label_match, confidence],
        )
        mlflow_run_id = evaluation.run_id
        print("MLflow evaluation run:", mlflow_run_id)
        print(evaluation.metrics)

        run_metrics = {
            "accuracy": float(accuracy),
            "weighted_precision": float(weighted_precision),
            "weighted_recall": float(weighted_recall),
            "weighted_f1": float(weighted_f1),
            "registry_prev_accuracy": float(previous_model_properties["accuracy"]),
            "test_samples": float(len(y_pred_argmax)),
            "traced_samples": float(trace_limit),
        }
        mlflow.log_metrics(run_metrics)
        confusion_frame = pd.DataFrame(
            confusion_matrix(y_test_argmax, y_pred_argmax),
            index=labels,
            columns=labels,
        ).astype(int)
        confusion_frame.index.name = "actual_label"
        mlflow.log_table(confusion_frame.reset_index(), artifact_file="confusion_matrix.json")
        mlflow.log_table(pd.DataFrame(prediction_rows), artifact_file="predictions.json")

        previous_runs = mlflow_client.search_runs(
            experiment_ids=_experiment_ids(),
            filter_string=f"tags.model_name = '{model_name}' and tags.evaluation = 'pipeline'",
            order_by=["attributes.start_time DESC"],
            max_results=20,
        )
        baseline_run = next(
            (item for item in previous_runs if item.info.run_id != mlflow_run_id),
            None,
        )
        if baseline_run is None:
            print("No previous evaluation run to compare")
        else:
            print("Comparing with baseline run:", baseline_run.info.run_id)
            comparison = mlflow.genai.compare_evaluations(
                candidate_run_id=mlflow_run_id,
                baseline_run_id=baseline_run.info.run_id,
                log_results=True,
            )
            summary = comparison.summary()
            print(summary.to_string())
            metrics.metadata["mlflow_baseline_run_id"] = baseline_run.info.run_id
            for _, row in summary.iterrows():
                scorer_name = str(row["scorer"]) if "scorer" in row.index else str(row.name)
                diff = row["diff"] if "diff" in row.index else None
                if diff is None or diff != diff:
                    continue
                metrics.log_metric(f"Compare {scorer_name} diff", float(diff))
                p_value = row["p_value"] if "p_value" in row.index else None
                if p_value is None or p_value != p_value:
                    continue
                metrics.log_metric(f"Compare {scorer_name} p", float(p_value))
    finally:
        if run_owner != "kfp":
            mlflow.end_run()

    metrics.metadata["mlflow_run_id"] = mlflow_run_id
    metrics.metadata["mlflow_run_owner"] = run_owner

    metrics.log_metric("Accuracy", float(accuracy))
    metrics.log_metric("Prev Model Accuracy", float(previous_model_properties["accuracy"]))
    metrics.log_metric("Weighted Precision", float(weighted_precision))
    metrics.log_metric("Weighted Recall", float(weighted_recall))
    metrics.log_metric("Weighted F1", float(weighted_f1))

    cmatrix = confusion_matrix(y_test_argmax,y_pred_argmax)
    cmatrix = cmatrix.tolist()
    targets = label_encoder_.classes_.tolist()
    classification_metrics.log_confusion_matrix(targets, cmatrix)
    
    if float(accuracy) <= 0.01: #float(previous_model_properties["accuracy"]):
        raise Exception("Accuracy is lower than the previous models")
        
@component(base_image="tensorflow/tensorflow:2.21.0", packages_to_install=["numpy<2", "onnxruntime==1.20.1", "pandas==2.2.3", "scikit-learn==1.6.1", "protobuf==7.34.0"])
def validate_onnx_model(
    onnx_model: Input[Artifact],
    keras_model: Input[Artifact],
    test_data: Input[Dataset],
    scaler: Input[Artifact],
):
    import onnxruntime as rt
    import pandas as pd
    import numpy as np
    import keras
    
    with open(test_data.path, 'rb') as pickle_file:
        X_test, _ = pd.read_pickle(pickle_file)
    with open(scaler.path, 'rb') as pickle_file:
        scaler_ = pd.read_pickle(pickle_file)
    _keras_model = keras.saving.load_model(keras_model.path)
    onnx_session = rt.InferenceSession(onnx_model.path, providers=rt.get_available_providers())

    test_inputs = {name: X_test[[name]].to_numpy() for name in X_test.columns}

    onnx_output_name = onnx_session.get_outputs()[0].name
    onnx_pred = onnx_session.run([onnx_output_name], test_inputs)
    
    keras_pred = _keras_model(test_inputs)
    
    print("Keras Pred: ", keras_pred)
    print("ONNX Pred: ", onnx_pred[0])
    
    for rt_res, keras_res in zip(onnx_pred[0], keras_pred):
        np.testing.assert_allclose(rt_res, keras_res, rtol=1e-5, atol=1e-5)

    print("Results match")
