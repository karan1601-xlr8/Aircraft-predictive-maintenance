"""
Train an LSTM model for Remaining Useful Life (RUL) prediction.

This script generates synthetic engine data using the existing project data generator,
trains a compact LSTM model, evaluates it, and saves model artifacts to ./models.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers


def build_dataset(seq_len=30, engines_per_status=120, cycles=80):
    """Generate synthetic sequence dataset and target RUL labels."""
    # Import existing generator from src.
    sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
    from inference import generate_example_data

    rows = []
    statuses = [
        ("healthy", 85),
        ("degrading", 55),
        ("critical", 25),
    ]

    for status, base_rul in statuses:
        for _ in range(engines_per_status):
            df = generate_example_data(num_cycles=cycles, health_status=status)

            # Use only base features expected by runtime inference.
            feature_cols = [
                c for c in df.columns if c.startswith("setting_") or c.startswith("sensor_")
            ]
            feat_df = df[feature_cols].copy()

            # Create multiple windows per engine and assign smoothly-decreasing RUL.
            max_start = len(feat_df) - seq_len
            for start in range(max_start + 1):
                end = start + seq_len
                seq_df = feat_df.iloc[start:end].copy()

                life_ratio = end / len(feat_df)
                synthetic_rul = max(5.0, base_rul - (life_ratio * 18.0) + np.random.normal(0, 3))

                rows.append((seq_df, synthetic_rul))

    return rows


def main():
    np.random.seed(42)
    keras.utils.set_random_seed(42)

    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "lstm_rul_model.keras")
    scaler_path = os.path.join(model_dir, "lstm_scaler.pkl")

    print("Building synthetic training dataset...")
    samples = build_dataset(seq_len=30, engines_per_status=120, cycles=80)

    # Keep feature names for runtime alignment through scaler.feature_names_in_.
    feature_cols = list(samples[0][0].columns)
    all_rows_df = pd.concat([s[0] for s in samples], ignore_index=True)

    scaler = MinMaxScaler()
    scaler.fit(all_rows_df[feature_cols])

    X, y = [], []
    for seq_df, target in samples:
        scaled_seq = scaler.transform(seq_df[feature_cols])
        X.append(scaled_seq)
        y.append(target)

    X = np.asarray(X, dtype=np.float32)
    y = np.asarray(y, dtype=np.float32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")
    print("Starting training...")

    model = keras.Sequential(
        [
            layers.Input(shape=(X.shape[1], X.shape[2])),
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(32),
            layers.Dropout(0.2),
            layers.Dense(16, activation="relu"),
            layers.Dense(1),
        ]
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=4,
            restore_best_weights=True,
        )
    ]

    model.fit(
        X_train,
        y_train,
        validation_split=0.2,
        epochs=20,
        batch_size=64,
        verbose=1,
        callbacks=callbacks,
    )

    test_loss, test_mae = model.evaluate(X_test, y_test, verbose=0)
    print(f"✅ Test Loss: {test_loss:.4f}")
    print(f"✅ Test MAE: {test_mae:.4f}")
    print("\n💾 Saving model...")

    model.save(model_path)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    print(f"✅ Model saved to {model_path}")
    print(f"✅ Scaler saved to {scaler_path}")


if __name__ == "__main__":
    main()
