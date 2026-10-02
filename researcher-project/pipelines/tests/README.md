# How to run

From `researcher-project/pipelines`:

```bash
PYTHONPATH=$(pwd) pytest tests/test_fetch_data.py
```

The test calls `fetch_data`, which needs the S3 connection environment variables and the `datasets/` objects in that bucket.
