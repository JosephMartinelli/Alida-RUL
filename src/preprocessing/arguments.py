import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input-folder", dest="input_folder", type=str, required=True)
parser.add_argument("--input-bucket", dest="input_bucket", type=str, required=True)
parser.add_argument(
    "--input-bucket.minIO_ACCESS_KEY",
    dest="bucket_access_key",
    type=str,
    required=True,
)
parser.add_argument(
    "--input-bucket.minIO_SECRET_KEY",
    dest="bucket_secret_key",
    type=str,
    required=True,
)
args, unknown = parser.parse_known_args()
