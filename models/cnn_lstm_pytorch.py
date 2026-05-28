"""
CNN-LSTM Hybrid Model for Stock Trading Signals
Uses PyTorch for deep learning predictions
Compatible with Python 3.14
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class CNNLSTMModel(nn.Module):
    """
    CNN-LSTM Hybrid Model for Stock Price Prediction
    Uses PyTorch for deep learning
    """
    
    def __init__(self, sequence_length: int = 60, n_features: int = 5):
        super(CNNLSTMModel, self).__init__()
        self.sequence_length = sequence_length
        self.n_features = n_features
        
        # CNN layers for feature extraction
        self.conv1 = nn.Conv1d(n_features, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        self.pool = nn.MaxPool1d(2)
        self.dropout1 = nn.Dropout(0.2)
        
        # LSTM layers
        self.lstm1 = nn.LSTM(128, 100, batch_first=True, dropout=0.2)
        self.lstm2 = nn.LSTM(100, 50, batch_first=True, dropout=0.2)
        self.dropout2 = nn.Dropout(0.2)
        
        # Dense layers
        self.fc1 = nn.Linear(50, 100)
        self.bn3 = nn.BatchNorm1d(100)
        self.dropout3 = nn.Dropout(0.3)
        self.fc2 = nn.Linear(100, 50)
        self.dropout4 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(50, 3)  # BUY, SELL, HOLD
        
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        # CNN: (batch, features, sequence) -> (batch, 128, sequence/2)
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = self.dropout1(x)
        
        # LSTM: (batch, sequence/2, 128) -> (batch, 50)
        x = x.permute(0, 2, 1)  # (batch, seq, features)
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        x = self.dropout2(x[:, -1, :])
        
        # Dense
        x = self.relu(self.fc1(x))
        x = self.bn3(x)
        x = self.dropout3(x)
        x = self.relu(self.fc2(x))
        x = self.dropout4(x)
        x = self.fc3(x)
        
        return self.softmax(x)


class PyTorchTrainer:
    """Trainer class for CNN-LSTM model"""
    
    def __init__(self, model, learning_rate=0.001):
        self.model = model
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5, min_lr=0.0001
        )
    
    def train_epoch(self, train_loader):
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for X, y in train_loader:
            self.optimizer.zero_grad()
            outputs = self.model(X)
            loss = self.criterion(outputs, y)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += y.size(0)
            correct += (predicted == y).sum().item()
        
        return total_loss / len(train_loader), correct / total
    
    def evaluate(self, val_loader):
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for X, y in val_loader:
                outputs = self.model(X)
                loss = self.criterion(outputs, y)
                
                total_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                total += y.size(0)
                correct += (predicted == y).sum().item()
        
        return total_loss / len(val_loader), correct / total
    
    def predict(self, X):
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X)
            probs = outputs.numpy()[0]
            signal_idx = np.argmax(probs)
            signals = ['BUY', 'SELL', 'HOLD']
            return {
                'signal': signals[signal_idx],
                'confidence': float(probs[signal_idx]),
                'probabilities': {
                    'BUY': float(probs[0]),
                    'SELL': float(probs[1]),
                    'HOLD': float(probs[2])
                }
            }


def prepare_data(df: pd.DataFrame, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare data for training"""
    features = ['open', 'high', 'low', 'close', 'volume']
    available = [f for f in features if f in df.columns]
    
    if len(available) < 5:
        return None, None
    
    data = df[available].values
    
    # Normalize
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data)
    
    # Create sequences
    X, y = [], []
    for i in range(sequence_length, len(scaled)):
        X.append(scaled[i-sequence_length:i].T)  # (features, sequence)
        
        # Create label based on future return
        future_return = (df['close'].iloc[min(i+5, len(df)-1)] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
        if future_return > 0.02:
            y.append(0)  # BUY
        elif future_return < -0.02:
            y.append(1)  # SELL
        else:
            y.append(2)  # HOLD
    
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.long)


def train_model(df: pd.DataFrame, epochs: int = 50, batch_size: int = 32) -> Dict:
    """Train the CNN-LSTM model"""
    if not TORCH_AVAILABLE:
        return {'status': 'PyTorch not available'}
    
    print("Preparing data...")
    X, y = prepare_data(df)
    
    if X is None:
        return {'status': 'Insufficient data'}
    
    print(f"Training samples: {len(X)}")
    
    # Split data
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
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
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Create model
    model = CNNLSTMModel(sequence_length=60, n_features=len(X_train.shape[1]))
    trainer = PyTorchTrainer(model)
    
    print("Training model...")
    best_val_acc = 0
    history = {'train_loss': [], 'val_loss': [], 'train_acc': [], 'val_acc': []}
    
    for epoch in range(epochs):
        train_loss, train_acc = trainer.train_epoch(train_loader)
        val_loss, val_acc = trainer.evaluate(val_loader)
        
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_acc'].append(train_acc)
        history['val_acc'].append(val_acc)
        
        trainer.scheduler.step(val_loss)
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'models/best_model.pth')
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2%}, Val Acc: {val_acc:.2%}")