import logging
import os
import tempfile

from minio import Minio, S3Error
import pandas as pd
import io


def minio_ls(
    address,
    access_key,
    secret_key,
    bucket_name,
    folder,
    extention_,
    use_ssl=False,
    use_exetention=True,
) -> list:

    if folder[-1] != "/":
        folder = folder + "/"

    cleaned = address.replace("http://", "").replace("https://", "")
    client = Minio(
        cleaned, access_key=access_key, secret_key=secret_key, secure=use_ssl
    )
    objects = client.list_objects(bucket_name=bucket_name, prefix=folder)
    to_return = []
    for x in objects:
        if (
            use_exetention
            and x.object_name.endswith(extention_)
            and not x.object_name.endswith("readme.txt")
        ):
            to_return.append(
                (
                    x.object_name,
                    client.get_object(
                        bucket_name=bucket_name, object_name=x.object_name
                    ),
                )
            )
        else:
            to_return.append(
                (
                    x.object_name,
                    client.get_object(
                        bucket_name=bucket_name, object_name=x.object_name
                    ),
                )
            )

    return to_return


def save_csv_to_minio(
    df: pd.DataFrame,
    df_name: str,
    output_minio_url,
    output_access_key,
    output_secret_key,
    output_minio_bucket,
    output_dataset,
):

    client = Minio(
        output_minio_url.replace("http://", "").replace("https://", ""),
        access_key=output_access_key,
        secret_key=output_secret_key,
        secure=False,
    )
    df_name = df_name.replace(".txt", ".csv")
    with tempfile.TemporaryDirectory() as tmpname:
        if "RUL" in df_name or "rul" in df_name:
            df.to_csv(
                f"{tmpname}/{df_name}",
                sep=";",
                header=False,
                index=False,
            )
        else:
            df.to_csv(
                f"{tmpname}/{df_name}",
                sep=" ",
                header=True,
                index=False,
            )
        print(
            "Uploading csv to minio",
            f"{tmpname}/{df_name} to {output_minio_bucket}/{output_dataset}/{df_name}",
        )
        client.fput_object(
            output_minio_bucket,
            output_dataset + "/" + df_name,
            f"{tmpname}/{df_name}",
            content_type="application/csv",
        )


def load_from_minio(
    minio_url: str,
    bucket_name: str,
    data_folder: str,
    access_key: str,
    secret_key: str,
) -> dict:
    files = minio_ls(
        address=minio_url,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        folder=data_folder,
        extention_=".txt",
        use_exetention=False,
    )
    dfs: dict = {}
    for file_name, file_obj in files:
        # skip irrelevant files
        if (
            not file_name.endswith(".txt")
            or "readme" in file_name.lower()
            or "x.txt" in file_name.lower()
        ):
            continue
        dataset_type, dataset_id = (
            file_name[file_name.rfind("/") + 1 :].replace(".txt", "").split("_", 1)
        )
        # map RUL files to a consistent key
        key = "RUL" if dataset_type.lower() == "rul" else dataset_type.lower()

        # initialize dict for this dataset_id if needed
        if dataset_id not in dfs:
            dfs[dataset_id] = {}

        # read CSV and assign to correct slot
        dfs[dataset_id][key] = (
            pd.read_csv(file_obj)
            if dataset_id == "RUL" or dataset_id == "rul"
            else pd.read_csv(file_obj, header=None, sep=" ")
        )

    return dfs
