from arguments import args
from utils import download_kaggle_dataset_to_bucket

if __name__ == "__main__":
    download_kaggle_dataset_to_bucket(
        kaggle_url=args.kaggle_url,
        minio_url=args.output_minio_url,
        bucket_name=args.output_minio_bucket,
        output_folder=args.output_dataset,
        access_key=args.output_access_key,
        secret_key=args.output_secret_key,
    )
