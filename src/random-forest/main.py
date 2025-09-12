from utils import load_from_minio, pickle_to_minio
from arguments import args
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
import matplotlib.pyplot as plt


def concat_data(
    dfs: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train: list[pd.DataFrame] = []
    test: list[pd.DataFrame] = []
    for data_key in dfs.keys():
        train.append(dfs[data_key]["train"])
        test.append(dfs[data_key]["test"])
    return pd.concat(train, ignore_index=True), pd.concat(test, ignore_index=True)


def save_model_and_params(estimator: RandomizedSearchCV, params: dict) -> None:
    # Save with pickle
    pickle_to_minio(
        estimator.best_params_,
        "params",
        args.output_model_minio_url,
        args.output_model_access_key,
        args.output_model_secret_key,
        args.output_model_minio_bucket,
        args.output_model,
    )
    pickle_to_minio(
        params,
        "random-forest-model",
        args.output_model_minio_url,
        args.output_model_access_key,
        args.output_model_secret_key,
        args.output_model_minio_bucket,
        args.output_model,
    )


def plot_true_vs_pred_life_ratio(y_test, y_pred):
    plt.figure(figsize=(8, 5))
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--")
    plt.xlabel("True life ration")
    plt.ylabel("Predicted life ratio")
    plt.title("Random Forest Predictions vs. True Values")
    plt.show()


def plot_unit_time_series(estimator, test_df, unit_id, target_col="life_ratio"):
    unit_data = test_df[test_df["unit_number"] == unit_id].copy()
    X_unit = unit_data.drop(
        columns=[target_col, "unit_number", "eol", "time_in_cycles"], errors="ignore"
    )
    y_true = unit_data[target_col].values
    y_pred = estimator.predict(X_unit)

    plt.figure(figsize=(8, 5))
    plt.plot(
        unit_data["time_in_cycles"], y_true, label=f"True {target_col}", marker="o"
    )
    plt.plot(
        unit_data["time_in_cycles"], y_pred, label=f"Pred {target_col}", marker="x"
    )
    plt.xlabel("Time in Cycles")
    plt.ylabel(target_col)
    plt.title(f"{target_col} over time for unit {unit_id}")
    plt.legend()
    plt.show()


def predict_life_ratio(
    clf: RandomizedSearchCV, train: pd.DataFrame, test: pd.DataFrame, param_dist: dict
) -> None:
    print(train.shape, test.shape)
    print(train.columns, test.columns)
    X_train = train.drop(
        columns=["RUL", "unit_number", "total_lifetime", "life_ratio", "time_in_cycles"]
    )
    y_train = train["life_ratio"]
    X_test = test.drop(columns=["life_ratio", "unit_number", "eol", "time_in_cycles"])
    y_test = test["life_ratio"]
    random_search = RandomizedSearchCV(
        clf,
        param_dist,
        cv=5,  # 5 folds
        scoring="neg_mean_squared_error",
        n_jobs=-1,
        verbose=1,
        n_iter=20,
    )
    random_search.fit(X_train, y_train)
    # Best hyperparameters
    print("Best parameters:", random_search.best_params_)
    # Best model
    best_rf = random_search.best_estimator_
    # Calculating metrics
    y_pred = best_rf.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Test MSE: {mse:.2f}")
    print(f"Test MAE: {mae:.2f}")
    print(f"Test RMSE: {rmse:.2f}")
    print(f"Test R²: {r2:.2f}")
    if args.show_plots:
        plot_true_vs_pred_life_ratio(y_test, y_pred)
        plot_unit_time_series(best_rf, test, 1)
    save_model_and_params(best_rf, random_search.best_params_)


def predict_RUL(
    clf: RandomForestRegressor,
    train: pd.DataFrame,
    test: pd.DataFrame,
    param_dist: dict,
):
    print(test.describe())
    print(test.head())
    print(test.columns)
    X_train = train.drop(columns=["RUL", "unit_number", "total_lifetime", "life_ratio"])
    y_train = train["RUL"]
    X_test = test.drop(
        columns=[
            "RUL",
            "unit_number",
            "total_lifetime",
            "life_ratio",
            "eol",
        ]
    )
    y_test = test["RUL"]
    print("Shapes:", X_train.shape, y_test.shape)
    random_search = RandomizedSearchCV(
        clf,
        param_distributions=param_dist,
        cv=5,
        scoring="neg_mean_squared_error",  # for regression
        n_jobs=-1,
        random_state=42,
        verbose=1,
    )
    random_search.fit(X_train, y_train)

    print("Best parameters:", random_search.best_params_)

    best_rf = random_search.best_estimator_
    y_pred = best_rf.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"Test MAE : {mae:.2f}")
    print(f"Test RMSE: {rmse:.2f}")
    print(f"Test R²  : {r2:.2f}")
    plt.figure(figsize=(7, 5))
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], "r--")
    plt.xlabel("True RUL")
    plt.ylabel("Predicted RUL")
    plt.title("Random Forest: Predictions vs True RUL")
    plt.show()
    unit_data = test[test["unit_number"] == 1].copy()
    X_unit = unit_data.drop(
        columns=[
            "RUL",
            "unit_number",
            "total_lifetime",
            "life_ratio",
            "eol",
        ]
    )
    y_unit_true = unit_data["RUL"].values

    # Predict RUL for this unit
    y_unit_pred = best_rf.predict(X_unit)

    # Plot true vs predicted RUL over time
    plt.figure(figsize=(8, 5))
    plt.plot(unit_data["time_in_cycles"], y_unit_true, label="True RUL", marker="o")
    plt.plot(
        unit_data["time_in_cycles"], y_unit_pred, label="Predicted RUL", marker="x"
    )
    plt.gca().invert_yaxis()  # optional: so RUL goes downward with time
    plt.xlabel("Time in Cycles")
    plt.ylabel("Remaining Useful Life (RUL)")
    plt.title(f"RUL Prediction for Unit {1}")
    plt.legend()
    plt.show()


if __name__ == "__main__":
    import logging

    logging.warning(str(args))
    dfs = load_from_minio(
        minio_url=args.input_minio_url,
        bucket_name=args.input_minio_bucket,
        data_folder=args.input_dataset,
        access_key=args.input_access_key,
        secret_key=args.input_secret_key,
    )
    train, test = concat_data(dfs)
    clf = RandomForestRegressor(n_estimators=15, random_state=42)
    param_dist = {
        "n_estimators": [5, 10, 15],
        "max_depth": [None, 10],
        "min_samples_split": [2, 4],
        "min_samples_leaf": [10, 2],
        "max_features": [None, "sqrt", "log2"],
    }
    # predict_life_ratio(clf, train, test, param_dist)
    predict_RUL(clf, train, test, param_dist)
