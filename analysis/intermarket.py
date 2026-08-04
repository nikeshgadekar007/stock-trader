"""
Intermarket Analysis & Regime Switching Engine
Tracks macro indicators (DXY, VIX, TNX, Crude, Gold) and switches strategies based on volatility regime
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class IntermarketAnalyzer:
    """Analyzes intermarket relationships and detects market regimes"""
    
    # Key intermarket tickers
    MACRO_TICKERS = {
        'SPY': 'S&P 500',
        'QQQ': 'Nasdaq 100',
        'DXY': 'US Dollar Index',
        'TNX': '10Y Treasury Yield',
        'VIX': 'Volatility Index',
        'GLD': 'Gold ETF',
        'USO': 'Crude Oil ETF',
        'IEF': '7-10Y Treasury Bond',
        'HYG': 'High Yield Corporate Bond',
        'EEM': 'Emerging Markets'
    }
    
    def __init__(self):
        self.macro_data = {}
        self.regime = None
        self.regime_score = 0
        self.intermarket_signals = {}
    
    def fetch_macro_data(self) -> Dict:
        """Fetch all macro indicators"""
        results = {}
        
        for ticker, name in self.MACRO_TICKERS.items():
            try:
                t = yf.Ticker(f"^{ticker}" if ticker in ['VIX', 'TNX', 'DXY'] else ticker)
                df = t.history(period='3mo', auto_adjust=True)
                
                if df.empty:
                    continue
                
                current = df['Close'].iloc[-1]
                change_1d = (df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100 if len(df) >= 2 else 0
                change_5d = (df['Close'].iloc[-1] / df['Close'].iloc[-5] - 1) * 100 if len(df) >= 5 else 0
                change_20d = (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100 if len(df) >= 20 else 0
                
                # Calculate trend
                sma_20 = df['Close'].rolling(20).mean().iloc[-1]
                sma_50 = df['Close'].rolling(50).mean().iloc[-1] if len(df) >= 50 else sma_20
                
                if current > sma_20 > sma_50:
                    trend = 'BULLISH'
                elif current < sma_20 < sma_50:
                    trend = 'BEARISH'
                else:
                    trend = 'NEUTRAL'
                
                # Calculate RSI
                delta = df['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.inf)
                rsi = 100 - (100 / (1 + rs))
                
                results[ticker] = {
                    'name': name,
                    'price': round(current, 2),
                    'change_1d': round(change_1d, 2),
                    'change_5d': round(change_5d, 2),
                    'change_20d': round(change_20d, 2),
                    'trend': trend,
                    'rsi': round(rsi.iloc[-1], 1) if not rsi.isna().all() else 50.0
                }
            except Exception as e:
                results[ticker] = {'name': name, 'error': str(e)}
        
        self.macro_data = results
        return results
    
    def detect_regime(self) -> Dict:
        """Detect current market regime using VIX and macro indicators"""
        if not self.macro_data:
            self.fetch_macro_data()
        
        vix_data = self.macro_data.get('VIX', {})
        spy_data = self.macro_data.get('SPY', {})
        dxy_data = self.macro_data.get('DXY', {})
        tnx_data = self.macro_data.get('TNX', {})
        
        vix = vix_data.get('price', 20)
        spy_change = spy_data.get('change_20d', 0)
        dxy_change = dxy_data.get('change_20d', 0)
        tnx_change = tnx_data.get('change_20d', 0)
        
        # VIX-based regime classification
        if vix < 15:
            vix_regime = 'LOW_VOL'
            vix_score = 1.0
        elif vix < 20:
            vix_regime = 'NORMAL'
            vix_score = 0.7
        elif vix < 30:
            vix_regime = 'ELEVATED'
            vix_score = 0.4
        else:
            vix_regime = 'HIGH_VOL'
            vix_score = 0.1
        
        # Determine market direction
        if spy_change > 3:
            direction = 'STRONG_BULL'
        elif spy_change > 0:
            direction = 'BULL'
        elif spy_change > -3:
            direction = 'BEAR'
        else:
            direction = 'STRONG_BEAR'
        
        # Determine recommended strategy
        if vix_regime in ['LOW_VOL', 'NORMAL'] and direction in ['STRONG_BULL', 'BULL']:
            strategy = 'MOMENTUM'
            strategy_desc = 'Ride trends, buy breakouts'
        elif vix_regime in ['LOW_VOL', 'NORMAL'] and direction in ['STRONG_BEAR', 'BEAR']:
            strategy = 'MEAN_REVERSION'
            strategy_desc = 'Buy dips, sell rips'
        elif vix_regime in ['ELEVATED', 'HIGH_VOL']:
            strategy = 'BREAKOUT'
            strategy_desc = 'Trade breakouts with tight stops'
        else:
            strategy = 'NEUTRAL'
            strategy_desc = 'Reduce position size, wait for clarity'
        
        # Calculate regime score (0-100)
        regime_score = vix_score * 50 + (0.5 if direction in ['BULL', 'STRONG_BULL'] else 0.3) * 50
        
        # Intermarket signals
        signals = []
        
        # DXY signal (inverse correlation with stocks)
        if dxy_change < -1 and direction in ['BULL', 'STRONG_BULL']:
            signals.append('✅ DXY falling → Bullish for stocks')
        elif dxy_change > 1 and direction in ['BEAR', 'STRONG_BEAR']:
            signals.append('⚠️ DXY rising → Bearish for stocks')
        
        # TNX signal (rising yields = pressure on growth)
        if tnx_change > 0.5 and direction in ['BEAR', 'STRONG_BEAR']:
            signals.append('⚠️ Yields rising → Pressure on growth stocks')
        elif tnx_change < -0.5 and direction in ['BULL', 'STRONG_BULL']:
            signals.append('✅ Yields falling → Supportive for stocks')
        
        # VIX signal
        if vix > 25:
            signals.append('⚠️ High VIX → Reduce position size')
        elif vix < 15:
            signals.append('✅ Low VIX → Favorable for trend following')
        
        self.regime = {
            'vix': vix,
            'vix_regime': vix_regime,
            'direction': direction,
            'strategy': strategy,
            'strategy_desc': strategy_desc,
            'regime_score': round(regime_score, 1),
            'signals': signals,
            'vix_score': vix_score
        }
        
        self.intermarket_signals = {
            'dxy_change': dxy_change,
            'tnx_change': tnx_change,
            'spy_change': spy_change,
            'vix': vix,
            'signals': signals
        }
        
        return self.regime
    
    def get_position_multiplier(self) -> float:
        """Get position size multiplier based on regime"""
        if not self.regime:
            self.detect_regime()
        
        vix_regime = self.regime.get('vix_regime', 'NORMAL')
        
        multipliers = {
            'LOW_VOL': 1.0,
            'NORMAL': 0.8,
            'ELEVATED': 0.5,
            'HIGH_VOL': 0.25
        }
        
        return multipliers.get(vix_regime, 0.5)
    
    def validate_signal(self, signal: str, symbol: str = None) -> Dict:
        """Validate a trading signal against macro conditions"""
        if not self.regime:
            self.detect_regime()
        
        direction = self.regime.get('direction', 'NEUTRAL')
        strategy = self.regime.get('strategy', 'NEUTRAL')
        signals = self.regime.get('signals', [])
        
        validation_score = 0
        warnings = []
        confirmations = []
        
        # Check signal alignment with market direction
        if signal == 'BUY':
            if direction in ['STRONG_BULL', 'BULL']:
                validation_score += 30
                confirmations.append(f'Market is {direction} → Aligned with BUY')
            elif direction in ['STRONG_BEAR', 'BEAR']:
                validation_score -= 25
                warnings.append(f'Buying against {direction} market')
        
        elif signal == 'SELL':
            if direction in ['STRONG_BEAR', 'BEAR']:
                validation_score += 30
                confirmations.append(f'Market is {direction} → Aligned with SELL')
            elif direction in ['STRONG_BULL', 'BULL']:
                validation_score -= 25
                warnings.append(f'Selling against {direction} market')
        
        # Check VIX
        vix = self.regime.get('vix', 20)
        if vix > 25:
            validation_score -= 10
            warnings.append(f'High VIX ({vix:.1f}) → Reduce position size')
        elif vix < 15:
            validation_score += 10
            confirmations.append(f'Low VIX ({vix:.1f}) → Favorable conditions')
        
        # Add intermarket signals
        for s in signals:
            if s.startswith('✅'):
                confirmations.append(s)
            elif s.startswith('⚠️'):
                warnings.append(s)
        
        # Determine validation
        if validation_score >= 20:
            validation = 'CONFIRMED'
        elif validation_score >= 0:
            validation = 'NEUTRAL'
        else:
            validation = 'WEAK'
        
        return {
            'validation': validation,
            'validation_score': validation_score,
            'regime': self.regime,
            'confirmations': confirmations,
            'warnings': warnings,
            'position_multiplier': self.get_position_multiplier()
        }
    
    def get_summary(self) -> Dict:
        """Get a summary of current market conditions"""
        if not self.macro_data:
            self.fetch_macro_data()
        if not self.regime:
            self.detect_regime()
        
        return {
            'macro_data': self.macro_data,
            'regime': self.regime,
            'position_multiplier': self.get_position_multiplier(),
            'timestamp': datetime.now().isoformat()
        }


if __name__ == "__main__":
    analyzer = IntermarketAnalyzer()
    summary = analyzer.get_summary()
    print(f"VIX: {summary['regime']['vix']}")
    print(f"Regime: {summary['regime']['vix_regime']}")
    print(f"Direction: {summary['regime']['direction']}")
    print(f"Strategy: {summary['regime']['strategy']} - {summary['regime']['strategy_desc']}")
    print(f"Position Multiplier: {summary['position_multiplier']}")
    print(f"Signals: {summary['regime']['signals']}")
