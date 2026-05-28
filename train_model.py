"""
CNN-LSTM Model Training Script
Run this after setting up Python 3.12 + TensorFlow
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("=" * 50)
print("Stock Trading CNN-LSTM Model Training")
print("=" * 50)

# Check TensorFlow
try:
    import tensorflow as tf
    print(f"✓ TensorFlow version: {tf.__version__}")
except ImportError:
    print("✗ TensorFlow not found!")
    print("Please run setup_ai.bat first")
    exit(1)

from models.cnn_lstm import CNNLSTMModel
from data.fetcher import fetch_stock_data

def prepare_training_data(symbols: list, days: int = 365) -> pd.DataFrame:
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

def train_model():
    """Train the CNN-LSTM model"""
    
    # Training symbols (diversified portfolio)
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',  # Tech
        'JPM', 'BAC', 'WFC',  # Finance
        'JNJ', 'PFE', 'UNH',  # Healthcare
        'XOM', 'CVX', 'COP',  # Energy
        'WMT', 'KO', 'PG'  # Consumer
    ]
    
    print("\n1. Fetching training data...")
    df = prepare_training_data(symbols, days=365)
    
    if df.empty:
        print("No data available for training")
        return None
    
    print(f"   Total samples: {len(df)}")
    
    print("\n2. Initializing CNN-LSTM model...")
    model = CNNLSTMModel(sequence_length=60, n_features=5)
    
    print("\n3. Preparing sequences...")
    X, y = model.prepare_data(df)
    
    if len(X) < 100:
        print("Not enough data for training")
        return None
    
    print(f"   Training samples: {len(X)}")
    
    # Split data
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    print("\n4. Training model (this may take 10-30 minutes)...")
    print("   Architecture: Conv1D → LSTM → Dense → Output")
    print("   Output: BUY / SELL / HOLD")
    
    history = model.train(
        X_train, y_train,
        X_val, y_val,
        epochs=50,
        batch_size=32
    )
    
    print("\n5. Training complete!")
    print(f"   Final accuracy: {history['accuracy'][-1]:.2%}")
    print(f"   Final validation accuracy: {history['val_accuracy'][-1]:.2%}")
    
    # Save model
    model_path = f"models/cnn_lstm_model_{datetime.now().strftime('%Y%m%d')}"
    model.save_model(model_path)
    print(f"\n6. Model saved to: {model_path}")
    
    return model

def evaluate_model(model, test_symbols: list = None):
    """Evaluate model on unseen data"""
    if test_symbols is None:
        test_symbols = ['TSLA', 'META', 'NFLX']
    
    print("\n" + "=" * 50)
    print("Model Evaluation")
    print("=" * 50)
    
    for symbol in test_symbols:
        try:
            print(f"\nTesting {symbol}...")
            stock_data = fetch_stock_data(symbol)
            df = stock_data.get('history_daily')
            
            if df is None or len(df) < 60:
                continue
            
            # Get last 60 days
            recent = df.tail(60)
            
            # Prepare input
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            features = ['open', 'high', 'low', 'close', 'volume']
            available = [f for f in features if f in recent.columns]
            
            scaled = scaler.fit_transform(recent[available].values)
            X = scaled.reshape(1, 60, len(available))
            
            # Predict
            prediction = model.predict(X)
            
            print(f"   Signal: {prediction['signal']}")
            print(f"   Confidence: {prediction['confidence']:.2%}")
            print(f"   Probabilities: BUY={prediction['probabilities']['BUY']:.2%}, "
                  f"SELL={prediction['probabilities']['SELL']:.2%}, "
                  f"HOLD={prediction['probabilities']['HOLD']:.2%}")
            
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Starting CNN-LSTM Training Pipeline")
    print("=" * 50)
    
    # Train model
    model = train_model()
    
    if model:
        # Evaluate on test stocks
        evaluate_model(model)
        
        print("\n" + "=" * 50)
        print("Training Complete!")
        print("=" * 50)
        print("\nNext steps:")
        print("1. Run the app: streamlit run app.py")
        print("2. The AI model will be used for predictions")
        print("3. Check the 'AI Model' page for model details")
    else:
        print("\nTraining failed. Check errors above.")