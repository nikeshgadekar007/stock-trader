"""
Train CNN-LSTM Model with Real Stock Data
Downloads data from Yahoo Finance and trains the model
"""
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore")

# Stock lists for training
LARGE_CAP_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "XOM", "JPM", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP",
    "KO", "COST", "AVGO", "LLY", "TMO", "WMT", "BAC", "CSCO", "ACN", "MCD",
    "ABT", "DHR", "CRM", "ADBE", "NKE", "TXN", "NEE", "PM", "BMY", "UNP",
    "RTX", "HON", "ORCL", "IBM", "AMGN", "QCOM", "INTC", "AMD", "NOW", "AMAT"
]

MID_CAP_STOCKS = [
    "SNAP", "SQ", "ROKU", "ZM", "DOCU", "CRWD", "NET", "DDOG", "SNOW", "PLTR",
    "COIN", "RIVN", "LCID", "F", "GM", "BA", "GE", "CAT", "DE", "MMM",
    "PYPL", "SQ", "SHOP", "UBER", "LYFT", "DASH", "ABNB", "DOORDASH", "GME", "AMC"
]

HIGH_VOLATILITY = [
    "TSLA", "NVDA", "AMD", "COIN", "RIVN", "LCID", "PLTR", "GME", "AMC", "BB",
    "SPCE", "DKNG", "NIO", "XPEV", "LCID", "FUVI", "SENS", "CTRM", "ASTR", "BALL"
]

def download_stock_data(symbol, period="2y", interval="1d"):
    """Download stock data from Yahoo Finance"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        df = stock.history(period=period, interval=interval)
        if len(df) > 200:
            df["Symbol"] = symbol
            return df
        return None
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return None

def download_all_stocks(symbols, max_stocks=50):
    """Download data for multiple stocks"""
    all_data = []
    count = 0
    for symbol in symbols:
        if count >= max_stocks:
            break
        print(f"Downloading {symbol} ({count+1}/{max_stocks})...")
        df = download_stock_data(symbol)
        if df is not None and len(df) > 200:
            all_data.append(df)
            count += 1
    return all_data

def prepare_training_data(all_data, sequence_length=60):
    """Prepare data for training"""
    from models.cnn_lstm_pytorch import add_technical_indicators, prepare_data
    
    X_list, y_list = [], []
    for df in all_data:
        X, y = prepare_data(df, sequence_length)
        if X is not None:
            X_list.append(X)
            y_list.append(y)
    
    if not X_list:
        return None, None
    
    X = np.concatenate(X_list, axis=0)
    y = np.concatenate(y_list, axis=0)
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    return X, y

def train_model(X, y, epochs=50, batch_size=64, learning_rate=0.0005):
    """Train the CNN-LSTM model"""
    import torch
    import torch.nn as nn
    from torch.utils.data import TensorDataset, DataLoader
    from models.cnn_lstm_pytorch import CNNLSTMModel, PyTorchTrainer
    
    # Split data
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Create data loaders
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.LongTensor(y_val)
    )
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Create model
    n_features = X.shape[1]
    model = CNNLSTMModel(sequence_length=60, n_features=n_features)
    trainer = PyTorchTrainer(model, learning_rate=learning_rate)
    
    # Training loop
    best_val_acc = 0
    patience = 10
    patience_counter = 0
    
    for epoch in range(epochs):
        train_loss, train_acc = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.validate(val_loader)
        trainer.scheduler.step()
        
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% - Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            # Save best model
            os.makedirs("models/trained", exist_ok=True)
            torch.save(model.state_dict(), "models/trained/best_model.pth")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    print(f"\nBest validation accuracy: {best_val_acc:.2f}%")
    return model

def main():
    print("=" * 60)
    print("STOCK TRADING MODEL TRAINING")
    print("=" * 60)
    
    # Combine all stocks
    all_symbols = list(set(LARGE_CAP_STOCKS + MID_CAP_STOCKS + HIGH_VOLATILITY))
    print(f"\nDownloading data for {len(all_symbols)} stocks...")
    
    # Download data
    all_data = download_all_stocks(all_symbols, max_stocks=50)
    print(f"\nDownloaded {len(all_data)} stocks successfully")
    
    if len(all_data) == 0:
        print("No data downloaded. Please check your internet connection.")
        return
    
    # Prepare data
    print("\nPreparing training data...")
    X, y = prepare_training_data(all_data)
    
    if X is None:
        print("Failed to prepare training data")
        return
    
    print(f"Training samples: {len(X)}")
    print(f"Features: {X.shape[1]}, Sequence length: {X.shape[2]}")
    print(f"Label distribution: Buy={np.sum(y==0)}, Sell={np.sum(y==1)}, Hold={np.sum(y==2)}")
    
    # Train model
    print("\nTraining model...")
    model = train_model(X, y, epochs=50, batch_size=64)
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("Model saved to: models/trained/best_model.pth")
    print("=" * 60)

if __name__ == "__main__":
    main()