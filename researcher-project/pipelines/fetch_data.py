import ssl
import kfp
import kfp.dsl as dsl
from kfp.dsl import (
    component,
    Input,
    Output,
    Dataset,
    Metrics,
)

@component(base_image='python:3.9', packages_to_install=["dask[dataframe]==2024.8.0", "s3fs==2025.2.0", "pandas==2.2.3", "boto3==1.40.76"])
def fetch_data(
    dataset: Output[Dataset]
):
    """
    Fetches data from URL
    """
    
    import pandas as pd
    import yaml
    from os import environ
    from boto3 import client

    s3_endpoint_url = environ.get('AWS_S3_ENDPOINT_MODEL')
    s3_access_key = environ.get('AWS_ACCESS_KEY_ID_MODEL')
    s3_secret_key = environ.get('AWS_SECRET_ACCESS_KEY_MODEL')
    s3_bucket_name = environ.get('AWS_S3_BUCKET_MODEL')
    s3_region = environ.get('AWS_DEFAULT_REGION_MODEL')

    s3_client = client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint_url,
        region_name=s3_region,
        verify=False
    )
    s3_client.download_file(s3_bucket_name, 'datasets/song_properties.parquet', 'song_properties.parquet')
    s3_client.download_file(s3_bucket_name, 'datasets/song_rankings.parquet', 'song_rankings.parquet')
    song_properties = pd.read_parquet('song_properties.parquet')
    song_rankings = pd.read_parquet('song_rankings.parquet')

    # song_properties = pd.read_parquet('https://github.com/rhoai-mlops/jukebox/raw/refs/heads/main/99-data_prep/song_properties.parquet')
    # song_rankings = pd.read_parquet('https://github.com/rhoai-mlops/jukebox/raw/refs/heads/main/99-data_prep/song_rankings.parquet')
    
    data = song_rankings.merge(song_properties, on='spotify_id', how='left')
    
    dataset.path += ".csv"
    dataset.metadata = {"song_properties": "https://github.com/rhoai-mlops/jukebox/raw/refs/heads/main/99-data_prep/song_properties.parquet", "song_rankings": "https://github.com/rhoai-mlops/jukebox/raw/refs/heads/main/99-data_prep/song_rankings.parquet" }
    data.to_csv(dataset.path, index=False, header=True)
