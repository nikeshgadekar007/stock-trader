"""
CNN-LSTM Model Training with PyTorch
Works with Python 3.14
"""

import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 50)
print("Stock Trading CNN-LSTM Training (PyTorch)")
print("=" * 50)

# Install PyTorch if needed
try:
    import torch
    print(f"[OK] PyTorch version: {torch.__version__}")
except ImportError:
    print("Installing PyTorch...")
    import subprocess
    subprocess.run(['pip', 'install', 'torch', '--index-url', 'https://download.pytorch.org/whl/cpu'])

from models.cnn_lstm_pytorch import CNNLSTMModel, PyTorchTrainer, prepare_data
from data.fetcher import fetch_stock_data

def prepare_training_data(symbols: list) -> pd.DataFrame:
    """Fetch and prepare training data"""
    all_data = []
    
    for symbol in symbols:
        try:
            print(f"Fetching {symbol}...")
            stock_data = fetch_stock_data(symbol)
            df = stock_data.get('history_daily')
            if df is not None and len(df) > 100:
                df['symbol'] = symbol
                all_data.append(df)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue
    
    if all_data:
        combined = pd.concat(all_data)
        return combined.sort_index()
    return pd.DataFrame()

def train():
    """Train the CNN-LSTM model"""
    
    # Training symbols
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
        'JPM', 'BAC', 'WFC',
        'JNJ', 'PFE', 'UNH',
        'XOM', 'CVX', 'COP',
        'WMT', 'KO', 'PG'
    ]
    
    print("\n1. Fetching training data...")
    df = prepare_training_data(symbols)
    
    if df.empty:
        print("No data available")
        return None
    
    print(f"   Total samples: {len(df)}")
    
    print("\n2. Preparing sequences...")
    X, y = prepare_data(df)
    
    if X is None:
        print("Not enough data")
        return None
    
    print(f"   Training samples: {len(X)}")
    
    # Split data
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    print("\n3. Creating model...")
    model = CNNLSTMModel(sequence_length=60, n_features=X_train.shape[1])
    trainer = PyTorchTrainer(model)
    
    print("\n4. Training (10-30 minutes)...")
    print("   Architecture: Conv1D -> LSTM -> Dense -> BUY/SELL/HOLD")
    
    from torch.utils.data import DataLoader, TensorDataset
    
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.LongTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.FloatTensor(X_val),
        torch.LongTensor(y_val)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    best_val_acc = 0
    
    for epoch in range(50):
        train_loss, train_acc = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.evaluate(val_loader)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'models/best_model.pth')
        
        if (epoch + 1) % 10 == 0:
            print(f"   Epoch {epoch+1}/50 - Val Acc: {val_acc:.2%}")
    
    print(f"\n5. Best validation accuracy: {best_val_acc:.2%}")
    print("   Model saved to: models/best_model.pth")
    
    return model

def test_model(model):
    """Test on unseen stocks"""
    print("\n" + "=" * 50)
    print("Testing Model")
    print("=" * 50)
    
    from torch.utils.data import DataLoader, TensorDataset
    from sklearn.preprocessing import MinMaxScaler
    
    test_symbols = ['TSLA', 'META', 'NFLX']
    
    for symbol in test_symbols:
        try:
            print(f"\n{symbol}:")
            stock_data = fetch_stock_data(symbol)
            df = stock_data.get('history_daily')
            
            if df is None or len(df) < 60:
                continue
            
            # Prepare input
            features = ['open', 'high', 'low', 'close', 'volume']
            available = [f for f in features if f in df.columns]
            
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(df[available].values)
            
            X = scaled[-60:].T.reshape(1, len(available), 60)
            X_tensor = torch.FloatTensor(X)
            
            # Predict
            model.eval()
            with torch.no_grad():
                output = model(X_tensor)
                probs = output.numpy()[0]
            
            signal_idx = np.argmax(probs)
            signals = ['BUY', 'SELL', 'HOLD']
            
            print(f"   Signal: {signals[signal_idx]}")
            print(f"   Confidence: {probs[signal_idx]:.2%}")
            print(f"   BUY: {probs[0]:.2%}, SELL: {probs[1]:.2%}, HOLD: {probs[2]:.2%}")
            
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    print("\nStarting PyTorch Training...")
    
    model = train()
    
    if model:
        test_model(model)
        
        print("\n" + "=" * 50)
        print("Training Complete!")
        print("=" * 50)
        print("\nNext: Run streamlit run app.py")
    else:
        print("\nTraining failed.")