"""CNN-LSTM Model for Stock Trading - Enhanced with Technical Indicators"""
import numpy as np
import pandas as pd
from typing import Tuple
import warnings
warnings.filterwarnings("ignore")

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class CNNLSTMModel(nn.Module):
    def __init__(self, sequence_length=60, n_features=15):
        super(CNNLSTMModel, self).__init__()
        self.conv1 = nn.Conv1d(n_features, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(128)
        self.conv3 = nn.Conv1d(128, 256, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(256)
        self.pool = nn.MaxPool1d(2)
        self.dropout1 = nn.Dropout(0.2)
        self.lstm1 = nn.LSTM(256, 128, batch_first=True, dropout=0.2)
        self.lstm2 = nn.LSTM(128, 64, batch_first=True, dropout=0.2)
        self.attention = nn.Linear(64, 1)
        self.dropout2 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(64, 128)
        self.bn4 = nn.BatchNorm1d(128)
        self.dropout3 = nn.Dropout(0.3)
        self.fc2 = nn.Linear(128, 64)
        self.dropout4 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(64, 3)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool(x)
        x = self.dropout1(x)
        x = x.permute(0, 2, 1)
        x, _ = self.lstm1(x)
        x, _ = self.lstm2(x)
        attention_weights = torch.softmax(self.attention(x), dim=1)
        x = (x * attention_weights).sum(dim=1)
        x = self.dropout2(x)
        x = self.relu(self.fc1(x))
        x = self.bn4(x)
        x = self.dropout3(x)
        x = self.relu(self.fc2(x))
        x = self.dropout4(x)
        x = self.fc3(x)
        return self.softmax(x)


class PyTorchTrainer:
    def __init__(self, model, learning_rate=0.0005):
        self.model = model
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
        self.scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(self.optimizer, T_0=10, T_mult=2)
    
    def train_epoch(self, train_loader):
        self.model.train()
        total_loss, correct, total = 0, 0, 0
        for X, y in train_loader:
            self.optimizer.zero_grad()
            outputs = self.model(X)
            loss = self.criterion(outputs, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += y.size(0)
            correct += (predicted == y).sum().item()
        return total_loss / len(train_loader), 100 * correct / total
    
    def validate(self, val_loader):
        self.model.eval()
        total_loss, correct, total = 0, 0, 0
        with torch.no_grad():
            for X, y in val_loader:
                outputs = self.model(X)
                loss = self.criterion(outputs, y)
                total_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                total += y.size(0)
                correct += (predicted == y).sum().item()
        return total_loss / len(val_loader), 100 * correct / total


def add_technical_indicators(df):
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss))
    ema_12 = df["Close"].ewm(span=12).mean()
    ema_26 = df["Close"].ewm(span=26).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    sma20 = df["Close"].rolling(20).mean()
    std20 = df["Close"].rolling(20).std()
    df["bb_upper"] = sma20 + (std20 * 2)
    df["bb_lower"] = sma20 - (std20 * 2)
    df["bb_position"] = (df["Close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    df["vwap"] = (typical_price * df["Volume"]).cumsum() / df["Volume"].cumsum()
    df["vwap_distance"] = (df["Close"] - df["vwap"]) / df["vwap"] * 100
    high_low = df["High"] - df["Low"]
    high_close = abs(df["High"] - df["Close"].shift())
    low_close = abs(df["Low"] - df["Close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["atr_percent"] = df["atr"] / df["Close"] * 100
    df["ema_9"] = df["Close"].ewm(span=9).mean()
    df["ema_21"] = df["Close"].ewm(span=21).mean()
    df["ema_9_21_ratio"] = df["ema_9"] / df["ema_21"]
    df["volume_ma"] = df["Volume"].rolling(20).mean()
    df["volume_ratio"] = df["Volume"] / df["volume_ma"]
    df["momentum_5"] = df["Close"].pct_change(5)
    low_14 = df["Low"].rolling(14).min()
    high_14 = df["High"].rolling(14).max()
    df["stoch_k"] = 100 * (df["Close"] - low_14) / (high_14 - low_14)
    return df


def prepare_data(df, sequence_length=60):
    if df is None or len(df) < sequence_length + 50:
        return None, None
    df = add_technical_indicators(df)
    features = ["Open", "High", "Low", "Close", "Volume", "rsi", "macd", "macd_signal", "macd_hist", "bb_position", "vwap_distance", "atr_percent", "ema_9_21_ratio", "volume_ratio", "momentum_5"]
    available = [f for f in features if f in df.columns]
    for f in available:
        df[f] = df[f].fillna(0)
    X, y = [], []
    for i in range(sequence_length, len(df) - 5):
        future_close = df["Close"].iloc[i + 5]
        current_close = df["Close"].iloc[i]
        change_pct = (future_close - current_close) / current_close * 100
        if change_pct > 1.0:
            label = 0
        elif change_pct < -1.0:
            label = 1
        else:
            label = 2
        seq = df[available].iloc[i-sequence_length:i].values
        if len(seq) == sequence_length:
            X.append(seq)
            y.append(label)
    if not X:
        return None, None
    X = np.array(X)
    y = np.array(y)
    mean = X.mean(axis=(0, 1))
    std = X.std(axis=(0, 1)) + 1e-8
    X = (X - mean) / std
    X = X.transpose(0, 2, 1)
    return X.astype(np.float32), y.astype(np.int64)