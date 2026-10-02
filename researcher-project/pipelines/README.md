# Training pipeline

Kubeflow pipeline for the jukebox model: fetch, validate, preprocess, train, convert to ONNX, evaluate, and register.

`fetch_data` downloads `datasets/song_properties.parquet` and `datasets/song_rankings.parquet` from the bucket in the S3 connection. The component reads `AWS_S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`, and `AWS_DEFAULT_REGION`.

`prod_train_save_pipeline.py` injects `aws-connection-models` into the model registration step, which uploads artifacts to that same connection when `prod_flag` is false.
