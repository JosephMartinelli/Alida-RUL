import os
from minio import Minio, S3Error
import logging


def sink(local_folder, minio_url, bucket_name, minio_path, access_key, secret_key):
    minio_client = Minio(
        minio_url.replace("http://", "").replace("https://", ""),
        access_key=access_key,
        secret_key=secret_key,
        secure=False,
    )
    # Check if the ALIDA's bucket exists
    if not minio_client.bucket_exists(bucket_name="alida"):
        raise RuntimeError("Cannot find alida's bucket!")

    for root, _, files in os.walk(local_folder):
        for file in files:
            local_file_path = os.path.join(root, file)
            # Calculate the relative path to preserve folder structure
            relative_path = os.path.relpath(local_file_path, local_folder)
            # Compose the target path in MinIO
            object_name = os.path.join(minio_path, relative_path).replace("\\", "/")
            # for Windows compatibility
            try:
                logging.warning(
                    f"Uploading to bucket {bucket_name}/{object_name} file {local_file_path}"
                )
                minio_client.fput_object(
                    bucket_name,
                    object_name,
                    local_file_path,
                )
                logging.info(f"Uploaded: {object_name}")
            except S3Error as e:
                logging.warning(f"Failed to upload {object_name}: {e}")