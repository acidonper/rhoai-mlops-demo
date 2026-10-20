# Workbench notebooks

Run these in order in a project workbench that has `aws-connection-models` attached. The sample workbench is [`../argocd/workbench.yaml`](../argocd/workbench.yaml). The model is `jukebox`: song features in, probability of popularity per country out.

| Notebook | What you do |
| --- | --- |
| `1-experiment_train.ipynb` | Install TensorFlow and Keras, load `song_properties.parquet` and `song_rankings.parquet` from the upstream jukebox data prep, train the network, and save the Keras model, ONNX model, scaler, and label encoder in the workbench. |
| `2-save_model.ipynb` | Upload those artifacts to the models bucket and register version `0.0.1` of `jukebox` in the model registry. |
| `3-request_model.ipynb` | Scale one song and POST it to the deployed InferenceService. |

## Values to set

In `2-save_model.ipynb`, set `username` to the project name (`project01`) and `cluster_domain` to the cluster apps domain. The notebook connects to `https://<username>-registry-rest.<cluster_domain>`. S3 credentials come from the workbench connection. Run the cells after those two values are set.

In `3-request_model.ipynb`, set `infer_endpoint` to the InferenceService route, for example `https://jukebox-<apps-domain>`. The request URL is `<infer_endpoint>/v2/models/jukebox/infer`. Apply [`../argocd/inferenceservice.yaml`](../argocd/inferenceservice.yaml) once a registered ONNX artifact is available at `models/jukebox`, and confirm the runtime and hardware profile in that file.

The last section of notebook 3 points at [`../pipelines/prod_train_save_pipeline.py`](../pipelines/prod_train_save_pipeline.py). Set `cluster_domain` there too, then submit the run from the workbench as described in [the pipeline README](../pipelines/README.md).

## Author

Asier Cidon @RedHat