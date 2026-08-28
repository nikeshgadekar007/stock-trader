"""
Walk-Forward Weight Optimizer - Auto-tunes layer weights from live data.

Approach:
1. Load signals from signal_outcomes.db (with 5d outcomes)
2. Train logistic regression: layer scores -> win probability
3. Validate via walk-forward (train on past, test on recent)
4. Save optimal weights to JSON
5. ConfluenceScorer applies them as multipliers on the next scan

Why logistic regression:
- Interpretable: each coefficient = layer importance
- Stable: no overfitting on small datasets
- Fast: trains in milliseconds
"""
import json
import os
import sqlite3
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from analysis.signal_tracker import DB_PATH, init_db


WEIGHTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'learned_weights.json')

MIN_SAMPLES_FOR_OPTIMIZATION = 30
WALK_FORWARD_TRAIN_PCT = 0.6
MIN_OOS_IMPROVEMENT = 0.05


class WeightOptimizer:
    """Walk-forward optimizer for confluence layer weights."""

    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = []
        self.training_metrics = {}
        self.oos_metrics = {}

    def load_signals(self, min_samples=MIN_SAMPLES_FOR_OPTIMIZATION,
                      days_back=180):
        """Load signals with outcomes from DB."""
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        c.execute('''SELECT layers_json, win_5d, win_10d, return_5d, score, max_score, grade
                     FROM signal_outcomes
                     WHERE entry_date >= ? AND win_5d IS NOT NULL
                       AND layers_json IS NOT NULL
                     ORDER BY entry_date''', (cutoff,))

        rows = c.fetchall()
        conn.close()

        signals = []
        for row in rows:
            layers_json, win_5d, win_10d, ret_5d, score, max_score, grade = row
            try:
                layers = json.loads(layers_json)
            except Exception:
                continue
            if not isinstance(layers, dict):
                continue
            signals.append({
                'layers': layers,
                'win_5d': bool(win_5d),
                'win_10d': bool(win_10d) if win_10d is not None else None,
                'return_5d': ret_5d,
                'score': score,
                'max_score': max_score,
                'grade': grade,
            })

        if len(signals) < min_samples:
            return []
        return signals

    def build_feature_matrix(self, signals):
        """Build X (features) and y (labels) from signals."""
        all_keys = set()
        for s in signals:
            all_keys.update(s['layers'].keys())
        feature_names = sorted(all_keys)

        X = []
        y = []
        for s in signals:
            row = []
            for k in feature_names:
                val = s['layers'].get(k)
                if val is None or not isinstance(val, (int, float)):
                    val = 5
                row.append(float(val))
            X.append(row)
            y.append(1 if s['win_5d'] else 0)

        return np.array(X), np.array(y), feature_names

    def train(self, signals):
        """Train logistic regression on signal data."""
        if not HAS_SKLEARN:
            return {'error': 'sklearn not available'}

        X, y, feature_names = self.build_feature_matrix(signals)
        self.feature_names = feature_names

        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = LogisticRegression(
            max_iter=1000,
            C=0.5,
            penalty='l2',
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X_scaled, y)

        train_acc = self.model.score(X_scaled, y)
        self.training_metrics = {
            'train_accuracy': round(train_acc * 100, 1),
            'n_samples': len(signals),
            'n_features': len(feature_names),
        }
        return self.training_metrics

    def walk_forward_validate(self, signals):
        """Train on first 60%, test on last 40%."""
        if not HAS_SKLEARN or len(signals) < 30:
            return {'error': 'insufficient data'}

        n = len(signals)
        split = int(n * WALK_FORWARD_TRAIN_PCT)
        train_signals = signals[:split]
        test_signals = signals[split:]

        X_train, y_train, _ = self.build_feature_matrix(train_signals)
        X_test, y_test, _ = self.build_feature_matrix(test_signals)

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        model = LogisticRegression(max_iter=1000, C=0.5, penalty='l2',
                                    random_state=42, class_weight='balanced')
        model.fit(X_train_s, y_train)

        train_acc = model.score(X_train_s, y_train)
        test_acc = model.score(X_test_s, y_test)

        baseline_acc = max(np.mean(y_test), 1 - np.mean(y_test))

        improvement = test_acc - baseline_acc

        self.oos_metrics = {
            'train_accuracy': round(train_acc * 100, 1),
            'test_accuracy_oos': round(test_acc * 100, 1),
            'baseline_accuracy': round(baseline_acc * 100, 1),
            'improvement_pct': round(improvement * 100, 1),
            'n_train': len(train_signals),
            'n_test': len(test_signals),
        }
        return self.oos_metrics

    def extract_weights(self):
        """Extract learned weights from trained model. Maps to layer multipliers."""
        if not self.model or not self.feature_names:
            return {}

        weights = {}
        coefs = self.model.coef_[0]

        raw_weights = {}
        for i, name in enumerate(self.feature_names):
            raw_weights[name] = coefs[i]

        all_positive = all(w >= 0 for w in raw_weights.values())

        if all_positive:
            max_abs = max(abs(w) for w in raw_weights.values()) or 1.0
            for name, w in raw_weights.items():
                multiplier = 0.5 + (w / max_abs) * 1.0
                multiplier = max(0.3, min(1.7, multiplier))
                weights[name] = round(multiplier, 3)
        else:
            for name, w in raw_weights.items():
                multiplier = 1.0 + w * 0.3
                multiplier = max(0.3, min(1.7, multiplier))
                weights[name] = round(multiplier, 3)

        return weights

    def get_layer_importance(self):
        """Return layers sorted by absolute importance."""
        if not self.model or not self.feature_names:
            return []

        coefs = self.model.coef_[0]
        importance = []
        for i, name in enumerate(self.feature_names):
            importance.append({
                'layer': name,
                'coefficient': round(float(coefs[i]), 4),
                'abs_importance': abs(float(coefs[i])),
                'direction': 'POSITIVE' if coefs[i] > 0 else 'NEGATIVE',
            })
        importance.sort(key=lambda x: -x['abs_importance'])
        return importance

    def run_optimization(self, days_back=180):
        """Full optimization pipeline: load, train, validate, decide."""
        signals = self.load_signals(days_back=days_back)
        if len(signals) < MIN_SAMPLES_FOR_OPTIMIZATION:
            return {
                'success': False,
                'error': 'insufficient_data',
                'n_signals': len(signals),
                'min_required': MIN_SAMPLES_FOR_OPTIMIZATION,
                'message': 'Need at least ' + str(MIN_SAMPLES_FOR_OPTIMIZATION) + ' resolved signals (5+ days old).'
            }

        train_metrics = self.train(signals)
        oos_metrics = self.walk_forward_validate(signals)
        learned_weights = self.extract_weights()
        importance = self.get_layer_importance()

        should_apply = False
        reason = ''
        if 'error' not in oos_metrics:
            if oos_metrics['improvement_pct'] >= MIN_OOS_IMPROVEMENT * 100:
                should_apply = True
                reason = 'OOS improvement of ' + str(oos_metrics['improvement_pct']) + '% beats baseline'
            else:
                reason = 'OOS improvement only ' + str(oos_metrics['improvement_pct']) + '%, below ' + str(int(MIN_OOS_IMPROVEMENT * 100)) + '% threshold'

        return {
            'success': True,
            'n_signals': len(signals),
            'train_metrics': train_metrics,
            'oos_metrics': oos_metrics,
            'weights': learned_weights,
            'importance': importance,
            'should_apply': should_apply,
            'reason': reason,
            'feature_names': self.feature_names,
            'timestamp': datetime.now().isoformat(),
        }

    def save_weights(self, weights, metadata=None):
        """Save learned weights to JSON."""
        data = {
            'weights': weights,
            'metadata': metadata or {},
            'saved_at': datetime.now().isoformat(),
        }
        with open(WEIGHTS_PATH, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_weights():
        """Load saved weights. Returns None if not found."""
        if not os.path.exists(WEIGHTS_PATH):
            return None
        try:
            with open(WEIGHTS_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def apply_to_score(base_scores, learned_weights):
        """Apply learned multipliers to base scores."""
        if not learned_weights:
            return {k: float(v) for k, v in base_scores.items()}
        adjusted = {}
        for layer, score in base_scores.items():
            mult = learned_weights.get(layer, 1.0)
            adjusted[layer] = float(score) * mult
        return adjusted


if __name__ == '__main__':
    print('Weight optimizer module')
    opt = WeightOptimizer()
    signals = opt.load_signals()
    print('Available signals with outcomes:', len(signals))
    if signals:
        result = opt.run_optimization()
        print('Should apply learned weights:', result.get('should_apply'))
        print('Reason:', result.get('reason'))