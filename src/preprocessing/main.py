import logging
from genericoutput import Log

if __name__ == "__main__":
    while True:
        # logging.warn(
        #     "input_dataset: %s,input_minio_bucket: %s,input_minio_url: %s, input_access_key: %s, input_secret_key: %s",
        #     args.input_dataset,
        #     args.input_minio_bucket,
        #     args.input_minio_url,
        #     args.input_access_key,
        #     args.input_secret_key,
        # )
        logging.warn("Printing to docker stream", flush=True)
        print("new version", flush=True)
