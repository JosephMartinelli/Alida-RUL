from minio import Minio, S3Error
import pandas as pd


def load_from_minio(
    minio_url: str,
    bucket_name: str,
    data_folder: str,
    access_key: str,
    secret_key: str,
    extension: str = ".csv",
) -> dict:
    files = minio_ls(
        address=minio_url,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        folder=data_folder,
        extention_=extension,
        use_exetention=False,
    )
    if not files:
        raise RuntimeError("No files found!")
    dfs: dict = {}
    for file_name, file_obj in files:
        # skip irrelevant files
        if (
            not file_name.endswith(extension)
            or "readme" in file_name.lower()
            or "x" + extension in file_name.lower()
        ):
            continue
        dataset_type, dataset_id = (
            file_name[file_name.rfind("/") + 1 :].replace(extension, "").split("_", 1)
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
            else pd.read_csv(file_obj, sep=" ", low_memory=False)
        )

    return dfs


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
