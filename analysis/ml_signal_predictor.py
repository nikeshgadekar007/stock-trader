"""Machine Learning Signal Predictor - Trains on historical indicators to predict outcomes"""
import numpy as np
import pandas as pd
from typing import Dict
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')


class MLSignalPredictor:
    """ML-based signal predictor using Random Forest and Gradient Boosting"""
    
    def __init__(self):
        self.rf_model = None
        self.gb_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.training_metrics = {}
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract ML features from price data"""
        features = pd.DataFrame(index=df.index)
        
        features['returns_1d'] = df['Close'].pct_change(1)
        features['returns_5d'] = df['Close'].pct_change(5)
        features['returns_10d'] = df['Close'].pct_change(10)
        features['returns_20d'] = df['Close'].pct_change(20)
        features['volatility_5d'] = df['Close'].pct_change().rolling(5).std()
        features['volatility_10d'] = df['Close'].pct_change().rolling(10).std()
        features['volatility_20d'] = df['Close'].pct_change().rolling(20).std()
        features['volume_ratio'] = df['Volume'] / df['Volume'].rolling(20).mean()
        features['volume_trend'] = df['Volume'].rolling(5).mean() / df['Volume'].rolling(20).mean()
        
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.inf)
        features['rsi'] = 100 - (100 / (1 + rs))
        
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']
        
        features['sma_10'] = df['Close'].rolling(10).mean()
        features['sma_20'] = df['Close'].rolling(20).mean()
        features['sma_50'] = df['Close'].rolling(50).mean()
        features['price_to_sma20'] = df['Close'] / features['sma_20']
        features['sma_10_20_ratio'] = features['sma_10'] / features['sma_20']
        
        bb_sma = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        features['bb_position'] = (df['Close'] - bb_sma) / (2 * bb_std)
        features['bb_width'] = (2 * bb_std) / bb_sma
        
        low_min = df['Low'].rolling(14).min()
        high_max = df['High'].rolling(14).max()
        features['stoch_k'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
        
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr'] = tr.rolling(14).mean()
        features['atr_pct'] = features['atr'] / df['Close']
        
        features['high_low_position'] = (df['Close'] - df['Low'].rolling(20).min()) / (df['High'].rolling(20).max() - df['Low'].rolling(20).min())
        features['momentum_5d'] = df['Close'] / df['Close'].shift(5) - 1
        features['momentum_10d'] = df['Close'] / df['Close'].shift(10) - 1
        
        features['target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
        self.feature_names = [col for col in features.columns if col != 'target']
        return features.dropna()
    
    def train(self, symbol: str = 'SPY', period: str = '2y') -> Dict:
        """Train ML models on historical data"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=True)
            if df.empty or len(df) < 100:
                return {'success': False, 'error': 'Insufficient data'}
            
            features_df = self._extract_features(df)
            if len(features_df) < 50:
                return {'success': False, 'error': 'Insufficient features'}
            
            X = features_df[self.feature_names].values
            y = features_df['target'].values
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            self.rf_model = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42)
            self.rf_model.fit(X_train_scaled, y_train)
            
            self.gb_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
            self.gb_model.fit(X_train_scaled, y_train)
            
            rf_pred = self.rf_model.predict(X_test_scaled)
            gb_pred = self.gb_model.predict(X_test_scaled)
            rf_proba = self.rf_model.predict_proba(X_test_scaled)[:, 1]
            gb_proba = self.gb_model.predict_proba(X_test_scaled)[:, 1]
            ensemble_proba = (rf_proba + gb_proba) / 2
            ensemble_pred = (ensemble_proba > 0.5).astype(int)
            
            self.training_metrics = {
                'rf_accuracy': round(accuracy_score(y_test, rf_pred) * 100, 1),
                'rf_precision': round(precision_score(y_test, rf_pred, zero_division=0) * 100, 1),
                'rf_recall': round(recall_score(y_test, rf_pred, zero_division=0) * 100, 1),
                'gb_accuracy': round(accuracy_score(y_test, gb_pred) * 100, 1),
                'gb_precision': round(precision_score(y_test, gb_pred, zero_division=0) * 100, 1),
                'gb_recall': round(recall_score(y_test, gb_pred, zero_division=0) * 100, 1),
                'ensemble_accuracy': round(accuracy_score(y_test, ensemble_pred) * 100, 1),
                'ensemble_precision': round(precision_score(y_test, ensemble_pred, zero_division=0) * 100, 1),
                'ensemble_recall': round(recall_score(y_test, ensemble_pred, zero_division=0) * 100, 1),
                'test_samples': len(y_test), 'train_samples': len(y_train), 'feature_count': len(self.feature_names)
            }
            self.is_trained = True
            return {'success': True, 'metrics': self.training_metrics}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict(self, df: pd.DataFrame) -> Dict:
        """Make prediction using trained models"""
        if not self.is_trained:
            return {'error': 'Model not trained', 'ml_signal': 'HOLD', 'ml_confidence': 0}
        
        try:
            features_df = self._extract_features(df)
            if len(features_df) == 0:
                return {'error': 'Cannot extract features', 'ml_signal': 'HOLD', 'ml_confidence': 0}
            
            latest = features_df[self.feature_names].iloc[-1:].values
            latest_scaled = self.scaler.transform(latest)
            
            rf_proba = self.rf_model.predict_proba(latest_scaled)[0][1]
            gb_proba = self.gb_model.predict_proba(latest_scaled)[0][1]
            ensemble_proba = (rf_proba + gb_proba) / 2
            
            if ensemble_proba > 0.65:
                ml_signal = 'BUY'
            elif ensemble_proba < 0.35:
                ml_signal = 'SELL'
            else:
                ml_signal = 'HOLD'
            
            return {
                'ml_signal': ml_signal,
                'ml_confidence': round(ensemble_proba * 100, 1),
                'rf_probability': round(rf_proba * 100, 1),
                'gb_probability': round(gb_proba * 100, 1),
                'feature_count': len(self.feature_names)
            }
        except Exception as e:
            return {'error': str(e), 'ml_signal': 'HOLD', 'ml_confidence': 0}
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance from Random Forest model"""
        if not self.is_trained or self.rf_model is None:
            return {}
        
        importances = self.rf_model.feature_importances_
        feature_importance = {}
        for name, importance in zip(self.feature_names, importances):
            feature_importance[name] = round(importance * 100, 2)
        
        sorted_features = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        return sorted_features
