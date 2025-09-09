from arguments import args
from utils import save_csv_to_minio, load_from_minio
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

columns = [
    "unit_number",
    "time_in_cycles",
    "setting_1",
    "setting_2",
    "TRA",
    "T2",
    "T24",
    "T30",
    "T50",
    "P2",
    "P15",
    "P30",
    "Nf",
    "Nc",
    "epr",
    "Ps30",
    "phi",
    "NRf",
    "NRc",
    "BPR",
    "farB",
    "htBleed",
    "Nf_dmd",
    "PCNfR_dmd",
    "W31",
    "W32",
]


def clean_dataframe(
    df: pd.DataFrame, show_plots: bool = False, train_df: bool = True
) -> pd.DataFrame:
    df.dropna(axis=1, how="all", inplace=True)
    if len(df.columns) <= 1:
        return df
    df.columns = columns
    # By previous statistical analysis we determine that the following columns do not carry any relevant info
    df.drop(
        columns=["Nf_dmd", "PCNfR_dmd", "P2", "T2", "TRA", "farB", "epr"],
        inplace=True,
    )
    if show_plots:
        sns.heatmap(df.corr(), annot=True, cmap="RdYlGn", linewidths=0.2)
        fig = plt.gcf()
        fig.set_size_inches(20, 20)
        plt.show()
    # We drop independent features that have very low correlation since they have low predicting power
    df.drop(columns=["setting_1", "setting_2"], inplace=True)
    return df


def preprocess_and_save(
    dfs: dict,
    minio_url: str,
    bucket_name: str,
    data_folder: str,
    access_key: str,
    secret_key: str,
    show_plots: bool = False,
) -> None:
    for df_key in dfs.keys():
        for df_type in dfs[df_key].keys():
            print(f"Analyzing {df_type}_{df_key}")
            cleaned_df_type = clean_dataframe(dfs[df_key][df_type], args.show_plots)

            # We define RUL as the number of remaining life cycles of a unit until failure
            # The training data provided by the CMAPS dataset contains engine data from run-to-failure
            # so the RUL will be the last cycle recorded (which is the max) minus the current cycle
            if df_type == "train":
                cleaned_df_type["RUL"] = (
                    cleaned_df_type.groupby("unit_number")["time_in_cycles"].transform(
                        "max"
                    )
                    - cleaned_df_type["time_in_cycles"]
                )
                cleaned_df_type["life_ratio"] = cleaned_df_type["time_in_cycles"] / (
                    cleaned_df_type.groupby("unit_number")["time_in_cycles"].transform(
                        "max"
                    )
                    - cleaned_df_type["time_in_cycles"]
                )
            # On the other hand the test set is truncated, where for each unit are shown the cycles up to some
            # cutoff point. The RUL_FD00X file shows the extra cycles left beyond the cutoff. So that means
            # that the RUL will be the last recorded cycle plus that value
            elif df_type == "test":
                # Map unit_number -> RUL from the file
                rul_map = dict(
                    zip(
                        cleaned_df_type["unit_number"].unique(),
                        dfs[df_key]["RUL"][0],
                    )
                )
                cleaned_df_type["eol"] = cleaned_df_type["unit_number"].map(rul_map)
                cleaned_df_type["life_ratio"] = cleaned_df_type["time_in_cycles"] / (
                    cleaned_df_type.groupby("unit_number")["time_in_cycles"].transform(
                        "max"
                    )
                    + cleaned_df_type["eol"]
                )
                cleaned_df_type.drop(columns=["eol"], inplace=True)
            save_csv_to_minio(
                df=cleaned_df_type,
                df_name=f"{df_type}_{df_key}.txt",
                output_minio_url=minio_url,
                output_access_key=access_key,
                output_secret_key=secret_key,
                output_minio_bucket=bucket_name,
                output_dataset=data_folder,
            )


if __name__ == "__main__":
    # Fetch raw dataset from MinIO
    import logging

    logging.warn(str(args))
    dfs = load_from_minio(
        minio_url=args.input_minio_url,
        bucket_name=args.input_minio_bucket,
        data_folder=args.input_dataset,
        access_key=args.input_access_key,
        secret_key=args.input_secret_key,
    )

    # Preprocess it and save it
    preprocess_and_save(
        dfs=dfs,
        minio_url=args.output_dataset_minio_url,
        bucket_name=args.output_dataset_minio_bucket,
        data_folder=args.output_dataset,
        access_key=args.output_dataset_access_key,
        secret_key=args.output_dataset_secret_key,
    )
