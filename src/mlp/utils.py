from minio import Minio, S3Error
import pandas as pd


def load_from_minio(
    minio_url: str,
    bucket_name: str,
    data_folder: str,
    access_key: str,
    secret_key: str,
) -> list[tuple[str, pd.DataFrame]]:
    files = minio_ls(
        address=minio_url,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        folder=data_folder,
        extention_=".txt",
        use_exetention=False,
    )
    if not files:
        raise FileNotFoundError(
            f"No files found at {minio_url}/{bucket_name}/{data_folder}"
        )
    dfs: list[tuple[str, pd.DataFrame]] = []
    for file_name, file_obj in files:
        if "readme.txt" in file_name:
            continue
        dfs.append((file_name, pd.read_csv(file_obj)))
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
