import os
import tempfile
import zipfile

import requests

from arguments import args
from utils import sink
#from alidaparse.input import InDatasetFactory


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
    :kaggle_url: URL of the Kaggle dataset
    :param minio_url: url to the minio deployment
    :param bucket_name: name of the bucket where to download the data to
    :param access_key: access key for the minio client
    :param secret_key: secret key for the minio client
    :param output_folder: name of the output dataset where to download the data to
    :return:
    """
    print(args)
    response = requests.get(kaggle_url)
    with tempfile.TemporaryDirectory() as tmpdirname:
        with open(f"{tmpdirname}/dataset.zip", "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(f"{tmpdirname}/dataset.zip", "r") as zip_ref:
            os.mkdir(f"{tmpdirname}/extracted")
            zip_ref.extractall(f"{tmpdirname}/extracted")
        extracted_dirs = os.listdir(f"{tmpdirname}/extracted")
        data_folder = (
            f"{tmpdirname}/extracted"
            if len(extracted_dirs) != 1
            else f"{tmpdirname}/extracted/" + extracted_dirs[0]
        )
        sink(
            local_folder=data_folder,
            minio_url=minio_url,
            bucket_name=bucket_name,
            minio_path=output_folder,
            access_key=access_key,
            secret_key=secret_key,
        )


if __name__ == "__main__":
    download_kaggle_dataset_to_bucket(
        kaggle_url=args.kaggle_url,
        minio_url=args.output_minio_url,
        bucket_name=args.output_minio_bucket,
        output_folder=args.output_dataset,
        access_key=args.output_access_key,
        secret_key=args.output_secret_key,
    )
