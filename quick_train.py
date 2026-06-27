"""
Quick Model Training - Uses pre-downloaded data or fewer stocks
"""
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# Fewer stocks for faster training
STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "JNJ",
    "PG", "MA", "HD", "UNH", "HD", "BAC", "XOM", "CVX", "PFE", "ABBV"
]

def download_stock_data(symbol, period="1y", interval="1d"):
    """Download stock data from Yahoo Finance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if len(df) > 100:
            df["Symbol"] = symbol
            return df
        return None
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return None

def main():
    print("=" * 60)
    print("QUICK STOCK TRADING MODEL TRAINING")
    print("=" * 60)
    
    all_data = []
    for i, symbol in enumerate(STOCKS):
        print(f"Downloading {symbol} ({i+1}/{len(STOCKS)})...")
        df = download_stock_data(symbol)
        if df is not None:
            all_data.append(df)
    
    print(f"\nDownloaded {len(all_data)} stocks")
    
    if len(all_data) < 5:
        print("Not enough data. Please check your internet connection.")
        return
    
    # Prepare data
    from models.cnn_lstm_pytorch import prepare_data
    
    X_list, y_list = [], []
    for df in all_data:
        X, y = prepare_data(df, sequence_length=30)  # Shorter sequence
        if X is not None:
            X_list.append(X)
            y_list.append(y)
    
    if not X_list:
        print("Failed to prepare training data")
        return
    
    X = np.concatenate(X_list, axis=0)
    y = np.concatenate(y_list, axis=0)
    
    print(f"Training samples: {len(X)}")
    print(f"Label distribution: Buy={np.sum(y==0)}, Sell={np.sum(y==1)}, Hold={np.sum(y==2)}")
    
    # Train model
    import torch
    from torch.utils.data import TensorDataset, DataLoader
    from models.cnn_lstm_pytorch import CNNLSTMModel, PyTorchTrainer
    
    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
    val_dataset = TensorDataset(torch.FloatTensor(X_val), torch.LongTensor(y_val))
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    model = CNNLSTMModel(sequence_length=30, n_features=X.shape[1])
    trainer = PyTorchTrainer(model, learning_rate=0.001)
    
    print("\nTraining...")
    for epoch in range(20):
        train_loss, train_acc = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.validate(val_loader)
        print(f"Epoch {epoch+1}/20 - Train: {train_acc:.1f}% - Val: {val_acc:.1f}%")
    
    os.makedirs("models/trained", exist_ok=True)
    torch.save(model.state_dict(), "models/trained/quick_model.pth")
    print("\nModel saved to models/trained/quick_model.pth")

if __name__ == "__main__":
    main()