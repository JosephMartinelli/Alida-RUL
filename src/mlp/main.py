import pandas as pd
from arguments import args
from utils import load_from_minio
import logging
from mlp import RULModel, RULDataset


import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import mean_squared_error
import numpy as np
import matplotlib.pyplot as plt

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def concat_data(
    dfs: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train: list[pd.DataFrame] = []
    test: list[pd.DataFrame] = []
    for data_key in dfs.keys():
        train.append(dfs[data_key]["train"])
        test.append(dfs[data_key]["test"])
    return pd.concat(train, ignore_index=True), pd.concat(test, ignore_index=True)


def evaluate_model(model, test_loader):
    # 3. Run inference
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            outputs = model(X_batch)
            all_preds.append(outputs.cpu().numpy())
            all_targets.append(y_batch.numpy())

    # 4. Calculate MSE
    preds = np.vstack(all_preds)
    targets = np.vstack(all_targets)
    mse = mean_squared_error(targets, preds)
    return mse


if __name__ == "__main__":
    logging.warn(str(args))
    dfs = load_from_minio(
        minio_url=args.input_minio_url,
        bucket_name=args.input_minio_bucket,
        data_folder=args.input_dataset,
        access_key=args.input_access_key,
        secret_key=args.input_secret_key,
    )
    train, test = concat_data(dfs)
    print(test.columns)
    print(train.columns)
    train.drop(columns=["unit_number", "life_ratio", "total_lifetime"], inplace=True)
    test.drop(
        columns=["unit_number", "life_ratio", "total_lifetime", "eol"], inplace=True
    )
    assert test.columns.tolist() == train.columns.tolist()
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    features = train.drop(columns=["RUL"])
    scaled_features = scaler.fit_transform(features)
    train.loc[:, features.columns] = scaled_features

    # Normalize test data using the same scaler
    test_features = test.drop(columns=["RUL"])
    test_scaled_features = scaler.transform(test_features)
    test.loc[:, test_features.columns] = test_scaled_features

    # 4. Dataset & Dataloader
    dataset = RULDataset(train)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Create TEST Dataset and DataLoader
    test_dataset = RULDataset(test)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # 5. Training Setup
    input_dim = train.shape[1] - 1  # Exclude RUL
    model = RULModel(input_dim).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)

    # 6. Training Loop
    best_mse = float("inf")
    epochs = 10
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            # Forward pass
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()

        val_mse = evaluate_model(model, test_loader)
        if val_mse < best_mse:
            best_mse = val_mse
            torch.save(model.state_dict(), "rul_ann_model.pth")

        print(
            f"Epoch [{epoch+1}/{epochs}], Loss: {running_loss/len(dataloader):.4f}, Test MSE: {val_mse:.4f}"
        )

    unit_id = 9  # Example unit number
    test = dfs["FD001"]["test"]
    unit_data = test[test["unit_number"] == unit_id]
    true_rul = unit_data["RUL"].values

    X_batch = scaler.transform(
        unit_data.drop(
            columns=["unit_number", "life_ratio", "total_lifetime", "eol", "RUL"]
        )
    )
    X_batch = torch.tensor(X_batch).float().to(device)
    model.eval()
    with torch.no_grad():
        pred_rul = model(X_batch).cpu().numpy().flatten()

    plt.figure(figsize=(8, 5))
    plt.plot(unit_data["time_in_cycles"], 1 - true_rul, label="True RUL", marker="o")
    plt.plot(
        unit_data["time_in_cycles"], 1 - pred_rul, label="Predicted RUL", marker="s"
    )
    plt.xlabel("Time in Cycles")
    plt.ylabel("Remaining Useful Life (RUL)")
    plt.title(f"Predicted vs True RUL for Unit {unit_id}")
    plt.legend()
    plt.show()
