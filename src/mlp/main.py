import pandas as pd
from utils import load_from_minio
from mlp import RULModel, RULDataset
from arguments import args
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import mean_squared_error
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def concat_data(
    dfs: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train: list[pd.DataFrame] = []
    test: list[pd.DataFrame] = []
    for data_key in dfs.keys():
        print("Processed", data_key)
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
    dfs = load_from_minio(
        minio_url=args.input_minio_url,
        bucket_name=args.input_minio_bucket,
        data_folder=args.input_dataset,
        access_key=args.input_access_key,
        secret_key=args.input_secret_key,
    )
    train,test = concat_data(dfs)

    scaler = StandardScaler()
    features = train.drop(columns=["life_ratio"])
    scaled_features = scaler.fit_transform(features)
    train.loc[:, features.columns] = scaled_features
    #
    # Normalize test data using the same scaler
    test_features = test.drop(columns=["life_ratio"])
    test_scaled_features = scaler.transform(test_features)
    test.loc[:, test_features.columns] = test_scaled_features
    #
    # 4. Dataset & Dataloader
    dataset = RULDataset(train)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Create TEST Dataset and DataLoader
    test_dataset = RULDataset(test)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    #
    # 5. Training Setup
    input_dim = train.shape[1] - 1  # Exclude RUL
    model = RULModel(input_dim).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=1e-4)

    # 6. Training Loop
    best_mse = float("inf")
    epochs = 50
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
    true_rul = unit_data["life_ratio"].values

    X_batch = scaler.transform(
        unit_data.drop(
            columns=["unit_number","time_in_cycles","eol","total_lifetime","RUL","life_ratio"]
        )
    )
    X_batch = torch.tensor(X_batch).float().to(device)
    model.eval()
    with torch.no_grad():
        pred_rul = model(X_batch).cpu().numpy().flatten()

    plt.figure(figsize=(8, 5))
    plt.plot(unit_data["time_in_cycles"], true_rul, label="True life_ratio", marker="o")
    plt.plot(
        unit_data["time_in_cycles"], pred_rul, label="Predicted life_ratio", marker="s"
    )
    plt.xlabel("Time in Cycles")
    plt.ylabel("life_ratio")
    plt.title(f"Predicted vs True liferatio for Unit {unit_id}")
    plt.legend()
    plt.show()
