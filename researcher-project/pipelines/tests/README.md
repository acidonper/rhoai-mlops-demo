# Fetch component test

`test_fetch_data.py` runs `fetch_data` with the Kubeflow local subprocess runner and checks the merged CSV columns. The component downloads real objects from S3. Nothing in the test mocks that call.

From `researcher-project/pipelines`:

```bash
pip install -r tests/requirements.txt
PYTHONPATH=$(pwd) pytest tests/test_fetch_data.py
```

Export the models-connection variables before pytest:

| Variable | Secret key on `aws-connection-models` |
| --- | --- |
| `AWS_S3_ENDPOINT_MODEL` | `AWS_S3_ENDPOINT` |
| `AWS_ACCESS_KEY_ID_MODEL` | `AWS_ACCESS_KEY_ID` |
| `AWS_SECRET_ACCESS_KEY_MODEL` | `AWS_SECRET_ACCESS_KEY` |
| `AWS_S3_BUCKET_MODEL` | `AWS_S3_BUCKET` |
| `AWS_DEFAULT_REGION_MODEL` | `AWS_DEFAULT_REGION` |

The bucket must contain `datasets/song_properties.parquet` and `datasets/song_rankings.parquet`. Those files are in [`../../datasets`](../../datasets). The test deletes `local_outputs` from the working directory (`researcher-project/pipelines`) when the run finishes.

`pytest.ini` ignores `DeprecationWarning`. `PYTHONPATH` is required so the test can import `fetch_data` from this directory.
