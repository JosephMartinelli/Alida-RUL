import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--output-dataset", dest="output_dataset", type=str, required=True)
parser.add_argument(
    "--output-dataset.minio_bucket",
    dest="output_dataset_minio_bucket",
    type=str,
    required=True,
)
parser.add_argument(
    "--output-dataset.minIO_URL",
    dest="output_dataset_minio_url",
    type=str,
    required=True,
)
parser.add_argument(
    "--output-dataset.minIO_ACCESS_KEY",
    dest="output_dataset_access_key",
    type=str,
    required=True,
)
parser.add_argument(
    "--output-dataset.minIO_SECRET_KEY",
    dest="output_dataset_secret_key",
    type=str,
    required=True,
)
parser.add_argument("--output-dataset.use_ssl", dest="use_ssl", type=str, default=False)

args, unknown = parser.parse_known_args()
