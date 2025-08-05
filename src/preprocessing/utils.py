import logging
import os
import tempfile
import zipfile

import requests
from minio import Minio, S3Error


def sink(local_folder, minio_url, bucket_name, minio_path, access_key, secret_key):
    minio_client = Minio(
        minio_url,
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
            object_name = os.path.join(minio_path, relative_path).replace(
                "\\", "/"
            )  # for Windows compatibility
            print(f"Uploading {local_file_path} to {bucket_name}/{object_name} ...")
            try:
                minio_client.fput_object(
                    bucket_name,
                    object_name,
                    local_file_path,
                )
                print(f"Uploaded: {object_name}")
            except S3Error as e:
                print(f"Failed to upload {object_name}: {e}")


def download_kaggle_dataset_to_bucket(
    kaggle_url: str,
    minio_url: str,
    bucket_name: str,
    output_folder: str,
    access_key: str,
    secret_key: str,
):
    """
    This function downloads the Cmaps dataset to the user MinIO bucket.
    :param minio_url: url to the minio deployment
    :param bucket_name: name of the bucket where to download the data to
    :param access_key: access key for the minio client
    :param secret_key: secret key for the minio client
    :param output_folder: name of the output dataset where to download the data to
    :return:
    """
    response = requests.get(kaggle_url)
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(f"{tmpdirname}/nasa-cmaps.zip", "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(f"{tmpdirname}/nasa-cmaps.zip", "r") as zip_ref:
            os.mkdir(f"{tmpdirname}/extracted")
            zip_ref.extractall(f"{tmpdirname}/extracted")
        sink(
            f"{tmpdirname}/extracted",
            minio_url=minio_url,
            bucket_name=bucket_name,
            minio_path=output_folder,
            access_key=access_key,
            secret_key=secret_key,
        )
