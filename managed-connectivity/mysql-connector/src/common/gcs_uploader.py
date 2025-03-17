"""Sends files to GCP storage."""
from typing import Dict
from google.cloud import storage

def upload(config: Dict[str, str], fileDirectory: str, filename: str, folder: str):
    """Uploads a file to GCS bucket."""
    client = storage.Client()
    bucket = client.get_bucket((config["output_bucket"]))

    blob = bucket.blob(f"{folder}/{filename}")
    blob.upload_from_filename(f"{fileDirectory}/{filename}")

def checkDestination(bucketpath: str):
    """Check GCS output folder exists"""
    client = storage.Client()

    if bucketpath.startswith("gs://"):
        print(f"Please provide output GCS path {bucketpath} without gs:// prefix")
        return False
    
    bucket = client.bucket(bucketpath)

    if not bucket.exists():
        print(f"Output GCS path {bucketpath} does not exist")
        return False
    
    return True
