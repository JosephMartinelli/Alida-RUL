import pandas as pd
import os
import minio

from arguments import args
import requests
import tempfile
import zipfile
import logging
from genericoutput import Log

from minio import Minio, S3Error

# columns = [
#     "unit_number",
#     "time_in_cycles",
#     "setting_1",
#     "setting_2",
#     "TRA",
#     "T2",
#     "T24",
#     "T30",
#     "T50",
#     "P2",
#     "P15",
#     "P30",
#     "Nf",
#     "Nc",
#     "epr",
#     "Ps30",
#     "phi",
#     "NRf",
#     "NRc",
#     "BPR",
#     "farB",
#     "htBleed",
#     "Nf_dmd",
#     "PCNfR_dmd",
#     "W31",
#     "W32",
# ]


if __name__ == "__main__":
    while True:
        Log(
            "input_dataset: %s,input_minio_bucket: %s,input_minio_url: %s, input_access_key: %s, input_secret_key: %s",
            args.input_dataset,
            args.input_minio_bucket,
            args.input_minio_url,
            args.input_access_key,
            args.input_secret_key,
        ).send()
