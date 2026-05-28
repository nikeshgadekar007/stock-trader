"""
CNN-LSTM Hybrid Model for Stock Trading Signals
Uses TensorFlow/Keras for deep learning predictions
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Try to import TensorFlow, handle if not available
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        Conv1D, MaxPooling1D, LSTM, Dense, Dropout, 
        BatchNormalization, Input, concatenate, Attention
    )
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class CNNLSTMModel:
    """
    CNN-LSTM Hybrid Model for Stock Price Prediction
    
    Architecture:
    - Input: Price data sequences (Open, High, Low, Close, Volume)
    - Conv1D: Feature extraction from local patterns
    - MaxPooling: Dimensionality reduction
    - LSTM: Temporal dependencies learning
    - Dense: Final prediction (BUY/SELL/HOLD)
    """
    
    def __init__(self, sequence_length: int = 60, n_features: int = 5):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        if not TF_AVAILABLE:
            print("Warning: TensorFlow not available. CNN-LSTM model will use fallback.")
    
    def build_model(self) -> Model:
        """Build CNN-LSTM hybrid architecture"""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for CNN-LSTM model")
        
        model = Sequential([
            # Input layer
            Input(shape=(self.sequence_length, self.n_features)),
            
            # CNN Feature Extraction
            Conv1D(filters=64, kernel_size=3, activation='relu', padding='same'),
            BatchNormalization(),
            Conv1D(filters=64, kernel_size=3, activation='relu', padding='same'),
            MaxPooling1D(pool_size=2),
            Dropout(0.2),
            
            # CNN Feature Extraction 2
            Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'),
            BatchNormalization(),
            Conv1D(filters=128, kernel_size=3, activation='relu', padding='same'),
            MaxPooling1D(pool_size=2),
            Dropout(0.2),
            
            # LSTM Layers
            LSTM(100, return_sequences=True),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            
            # Dense Layers
            Dense(100, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(50, activation='relu'),
            Dropout(0.2),
            Dense(3, activation='softmax')  # BUY, SELL, HOLD
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training"""
        # Features: OHLCV
        features = ['open', 'high', 'low', 'close', 'volume']
        
        # Check if all features exist
        available_features = [f for f in features if f in df.columns]
        if len(available_features) < 5:
            # Use available features
            data = df[available_features].values
        else:
            data = df[features].values
        
        # Normalize data
        from sklearn.preprocessing import MinMaxScaler
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = self._create_sequences(scaled_data)
        
        # Create labels based on future returns
        labels = self._create_labels(df)
        
        return X, labels
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM input"""
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
        return np.array(X), np.array(y)
    
    def _create_labels(self, df: pd.DataFrame) -> np.ndarray:
        """Create labels: 0=BUY, 1=SELL, 2=HOLD"""
        if 'close' not in df.columns:
            return np.zeros(len(df) - self.sequence_length)
        
        close = df['close'].values
        labels = []
        
        for i in range(self.sequence_length, len(close)):
            if i >= len(close):
                break
            
            # Calculate future return (next 5 days)
            future_return = 0
            if i + 5 < len(close):
                future_return = (close[i + 5] - close[i]) / close[i]
            
            # Label based on return
            if future_return > 0.02:  # >2% gain
                labels.append([1, 0, 0])  # BUY
            elif future_return < -0.02:  # >2% loss
                labels.append([0, 1, 0])  # SELL
            else:
                labels.append([0, 0, 1])  # HOLD
        
        return np.array(labels)
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None,
              epochs: int = 50, batch_size: int = 32) -> Dict:
        """Train the model"""
        if not TF_AVAILABLE:
            return {'status': 'TensorFlow not available'}
        
        if self.model is None:
            self.build_model()
        
        callbacks = [
            EarlyStopping(monitor='val_loss' if X_val is not None else 'loss', 
                        patience=10, restore_best_weights=True),
            ReduceLROnPlateau(monitor='val_loss' if X_val is not None else 'loss',
                            factor=0.5, patience=5, min_lr=0.0001)
        ]
        
        validation_data = (X_val, y_val) if X_val is not None else None
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        return history.history
    
    def predict(self, X: np.ndarray) -> Dict:
        """Make predictions"""
        if not TF_AVAILABLE or self.model is None:
            return {'signal': 'HOLD', 'confidence': 0.33, 'probabilities': [0.33, 0.33, 0.34]}
        
        predictions = self.model.predict(X, verbose=0)
        buy_prob, sell_prob, hold_prob = predictions[0]
        
        signal = 'BUY' if buy_prob > sell_prob and buy_prob > hold_prob else \
                'SELL' if sell_prob > buy_prob and sell_prob > hold_prob else 'HOLD'
        
        return {
            'signal': signal,
            'confidence': max(buy_prob, sell_prob, hold_prob),
            'probabilities': {
                'BUY': float(buy_prob),
                'SELL': float(sell_prob),
                'HOLD': float(hold_prob)
            }
        }
    
    def save_model(self, path: str):
        """Save model to disk"""
        if TF_AVAILABLE and self.model is not None:
            self.model.save(path)
    
    def load_model(self, path: str):
        """Load model from disk"""
        if TF_AVAILABLE:
            self.model = tf.keras.models.load_model(path)
            self.is_trained = True


class EnsembleModel:
    """Ensemble of multiple models for better predictions"""
    
    def __init__(self):
        self.models = []
        self.weights = []
    
    def add_model(self, model, weight: float = 1.0):
        """Add a model to ensemble"""
        self.models.append(model)
        self.weights.append(weight)
    
    def predict(self, X: np.ndarray) -> Dict:
        """Ensemble prediction"""
        if not self.models:
            return {'signal': 'HOLD', 'confidence': 0.5}
        
        weighted_probs = np.zeros(3)
        total_weight = 0
        
        for model, weight in zip(self.models, self.weights):
            try:
                pred = model.predict(X)
                probs = pred.get('probabilities', [0.33, 0.33, 0.34])
                weighted_probs += np.array(probs) * weight
                total_weight += weight
            except Exception:
                continue
        
        if total_weight == 0:
            return {'signal': 'HOLD', 'confidence': 0.5}
        
        weighted_probs /= total_weight
        
        signal = 'BUY' if weighted_probs[0] > weighted_probs[1] else 'SELL' if weighted_probs[1] > weighted_probs[0] else 'HOLD'
        
        return {
            'signal': signal,
            'confidence': float(max(weighted_probs)),
            'probabilities': {
                'BUY': float(weighted_probs[0]),
                'SELL': float(weighted_probs[1]),
                'HOLD': float(weighted_probs[2])
            }
        }
