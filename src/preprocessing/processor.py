from minio import Minio
from arguments import args
import pandas as pd
import requests


def minio_ls(
    address, access_key, secret_key, bucket_name, folder, extention, use_ssl=False
) -> list:

    if folder[-1] != "/":
        folder = folder + "/"

    client = Minio(
        address, access_key=access_key, secret_key=secret_key, secure=use_ssl
    )
    objects = client.list_objects(bucket_name=bucket_name, prefix=folder)

    files_list = [
        x._object_name
        for x in objects
        if extention in x._object_name[-len(extention) :]
    ]
    if len(files_list) > 1:
        return ["s3://" + bucket_name + "/" + x for x in files_list]
    elif len(files_list) == 1:
        return "s3://" + bucket_name + "/" + files_list[0]
    else:
        raise Exception("Dataset is empty!")


def process():

    storage_options = {
        "key": args.input_access_key,
        "secret": args.input_secret_key,
        "client_kwargs": {"endpoint_url": f"{args.input_minio_url}"},
    }
    file_path = minio_ls(
        args.input_minio_url,
        args.input_access_key,
        args.input_secret_key,
        args.input_minio_bucket,
        args.input_dataset,
        ".csv",
    )
    # dataset = pd.read_csv(file_path, storage_options=storage_options)
    return file_path[0].describe()
