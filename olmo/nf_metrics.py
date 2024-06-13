from typing import Any, Dict, Optional
import boto3
import os
import logging

log = logging.getLogger(__name__)

class NFMetrics:
    def __init__(self, metrics_file: str, checkpoint_location):
        self.metrics_file = metrics_file
        self.checkpoint_location = checkpoint_location

        s3 = boto3.resource('s3')
        bucket, key = self.split_s3_uri(self.checkpoint_location)
        filename = os.path.join(key, os.path.basename(self.metrics_file))

        checkpoint_exists = False
        try:
            s3.Object(bucket, filename).load()
            checkpoint_exists = True
        except Exception as e:
            log.warn(f"{filename} does not exist in {bucket}.")

        if checkpoint_exists:
            try:
                log.info(f"Downloading metrics file from S3: {bucket}/{filename}")
                s3.download_file(bucket, filename, self.metrics_file)
                log.info(f"Downloaded metrics file from S3: {bucket}/{filename}")
            except Exception as e:
                log.error(f"Error downloading metrics file from S3: {e}.")

    def log(self, data: Dict[str, Any], step: int):
        with open(self.metrics_file, "a") as f:
            wrapped_data = {
                "metrics": data,
                "step": step,
            }
            f.write(f"{wrapped_data}\n")
    
    def split_s3_uri(self, s3_uri: str):
        assert s3_uri.startswith('s3://')
        s3_parts = s3_uri[5:].split('/', 1)
        bucket = s3_parts[0]
        key = s3_parts[1] if len(s3_parts) > 1 else None
        return bucket, key

    def checkpoint(self):
        # Upload the metrics file to S3
        s3  = boto3.client('s3')
        if os.path.exists(self.metrics_file):
            try:
                bucket, key = self.split_s3_uri(self.checkpoint_location)
                filename = os.path.join(key, os.path.basename(self.metrics_file))
                log.info(f"Uploading metrics file to S3: {bucket}/{filename}")
                s3.upload_file(self.metrics_file, bucket, filename)
                log.info(f"Uploaded metrics file to S3: {bucket}/{filename}")
            except Exception as e:
                log.error(f"Error uploading metrics file to S3: {e}. Skipping checkpointing.")
        else:
            log.warning(f"Metrics file {self.metrics_file} does not exist. Skipping checkpointing.")
