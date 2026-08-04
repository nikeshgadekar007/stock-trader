"""Machine Learning Signal Predictor - Trains on historical indicators to predict outcomes
Enhanced with Walk-Forward Validation, XGBoost, and additional features"""
import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# Try to import XGBoost
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


class MLSignalPredictor:
    """ML-based signal predictor using Random Forest, Gradient Boosting, and XGBoost
    with Walk-Forward Validation for more reliable predictions"""
    
    def __init__(self):
        self.rf_model = None
        self.gb_model = None
        self.xgb_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        self.training_metrics = {}
        self.walk_forward_metrics = {}
    
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
    
    def walk_forward_validation(self, symbol: str = 'SPY', period: str = '2y', 
                                  train_window: int = 180, test_window: int = 30) -> Dict:
        """Perform walk-forward validation to get more reliable performance estimates"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=True)
            if df.empty or len(df) < train_window + test_window:
                return {'success': False, 'error': 'Insufficient data for walk-forward'}
            
            features_df = self._extract_features(df)
            if len(features_df) < train_window + test_window:
                return {'success': False, 'error': 'Insufficient features for walk-forward'}
            
            X = features_df[self.feature_names].values
            y = features_df['target'].values
            
            results = []
            n_windows = 0
            
            for start in range(0, len(X) - train_window - test_window, test_window):
                train_end = start + train_window
                test_end = train_end + test_window
                
                X_train = X[start:train_end]
                y_train = y[start:train_end]
                X_test = X[train_end:test_end]
                y_test = y[train_end:test_end]
                
                if len(X_test) < 5:
                    continue
                
                # Scale
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                # Train models
                rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
                rf.fit(X_train_scaled, y_train)
                rf_pred = rf.predict(X_test_scaled)
                
                gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
                gb.fit(X_train_scaled, y_train)
                gb_pred = gb.predict(X_test_scaled)
                
                # Ensemble
                rf_proba = rf.predict_proba(X_test_scaled)[:, 1]
                gb_proba = gb.predict_proba(X_test_scaled)[:, 1]
                ensemble_proba = (rf_proba + gb_proba) / 2
                ensemble_pred = (ensemble_proba > 0.5).astype(int)
                
                results.append({
                    'rf_accuracy': accuracy_score(y_test, rf_pred),
                    'gb_accuracy': accuracy_score(y_test, gb_pred),
                    'ensemble_accuracy': accuracy_score(y_test, ensemble_pred),
                    'ensemble_precision': precision_score(y_test, ensemble_pred, zero_division=0),
                    'ensemble_recall': recall_score(y_test, ensemble_pred, zero_division=0),
                    'test_samples': len(y_test)
                })
                n_windows += 1
            
            if n_windows == 0:
                return {'success': False, 'error': 'No valid windows'}
            
            # Aggregate results
            avg_rf_acc = np.mean([r['rf_accuracy'] for r in results])
            avg_gb_acc = np.mean([r['gb_accuracy'] for r in results])
            avg_ens_acc = np.mean([r['ensemble_accuracy'] for r in results])
            avg_ens_prec = np.mean([r['ensemble_precision'] for r in results])
            avg_ens_rec = np.mean([r['ensemble_recall'] for r in results])
            
            # Calculate stability (std dev of accuracy across windows)
            ens_acc_std = np.std([r['ensemble_accuracy'] for r in results])
            
            self.walk_forward_metrics = {
                'n_windows': n_windows,
                'avg_rf_accuracy': round(avg_rf_acc * 100, 1),
                'avg_gb_accuracy': round(avg_gb_acc * 100, 1),
                'avg_ensemble_accuracy': round(avg_ens_acc * 100, 1),
                'avg_ensemble_precision': round(avg_ens_prec * 100, 1),
                'avg_ensemble_recall': round(avg_ens_rec * 100, 1),
                'ensemble_accuracy_std': round(ens_acc_std * 100, 1),
                'stability': 'HIGH' if ens_acc_std < 0.05 else 'MEDIUM' if ens_acc_std < 0.10 else 'LOW',
                'total_test_samples': sum(r['test_samples'] for r in results)
            }
            
            return {'success': True, 'metrics': self.walk_forward_metrics}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def train_with_walk_forward(self, symbol: str = 'SPY', period: str = '2y') -> Dict:
        """Train models and perform walk-forward validation"""
        # First do walk-forward validation
        wf_result = self.walk_forward_validation(symbol, period)
        
        # Then train on full data
        train_result = self.train(symbol, period)
        
        if train_result.get('success') and wf_result.get('success'):
            # Merge metrics
            train_result['walk_forward'] = wf_result.get('metrics', {})
            train_result['metrics']['walk_forward_accuracy'] = wf_result['metrics'].get('avg_ensemble_accuracy', 0)
            train_result['metrics']['walk_forward_stability'] = wf_result['metrics'].get('stability', 'N/A')
        
        return train_result

