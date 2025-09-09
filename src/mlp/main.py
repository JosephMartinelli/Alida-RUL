import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from arguments import args
from utils import load_from_minio
import logging
from mlp import RULModel, RULDataset

if __name__ == "__main__":
    logging.warn(str(args))
    dfs = load_from_minio(
        minio_url=args.input_minio_url,
        bucket_name=args.input_minio_bucket,
        data_folder=args.input_dataset,
        access_key=args.input_access_key,
        secret_key=args.input_secret_key,
    )
    train_data = pd.concat(dfs, ignore_index=True)
