"""
Trading Signals and Position Sizing
Generates buy/sell signals with entry/exit prices
"""

from typing import Dict, Optional
import config


class TradeSignalGenerator:
    """Generates trading signals with entry/exit prices"""
    
    def __init__(self):
        self.capital = config.CAPITAL
        self.max_risk_per_trade = config.MAX_RISK_PER_TRADE
        self.max_concurrent_trades = config.MAX_CONCURRENT_TRADES
        
    def calculate_position_size(self, entry_price: float, stop_loss_pct: float = None) -> Dict:
        """Calculate position size based on risk"""
        if stop_loss_pct is None:
            stop_loss_pct = config.DEFAULT_STOP_LOSS_PCT
            
        risk_amount = self.max_risk_per_trade
        risk_per_share = entry_price * stop_loss_pct
        shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        total_cost = shares * entry_price
        
        if total_cost > self.capital:
            shares = int(self.capital / entry_price)
            total_cost = shares * entry_price
        
        return {
            'shares': shares,
            'entry_price': entry_price,
            'total_cost': total_cost,
            'risk_amount': risk_amount,
            'risk_per_share': risk_per_share,
            'stop_loss_pct': stop_loss_pct
        }
    
    def generate_buy_signal(self, quote: Dict, indicators: Dict) -> Optional[Dict]:
        """Generate buy signal"""
        signals = indicators.get('signals', {})
        buy_signals = signals.get('buy', [])
        
        # Also check for oversold conditions
        rsi = indicators.get('rsi', {})
        stoch = indicators.get('stochastic', {})
        
        if rsi.get('rsi', 50) < 40:
            buy_signals.append('RSI at ' + f"{rsi['rsi']:.1f}")
        if stoch.get('signal') == 'oversold':
            buy_signals.append('Stochastic Oversold')
        
        # Check for bullish MACD
        macd = indicators.get('macd', {})
        if macd.get('histogram', 0) > 0:
            buy_signals.append('MACD Bullish')
        
        if len(buy_signals) < 1:
            return None
        
        current_price = quote.get('current_price', 0)
        if not current_price:
            return None
        
        entry_price = round(current_price * 0.995, 2)
        stop_loss = round(entry_price * (1 - config.DEFAULT_STOP_LOSS_PCT), 2)
        take_profit = round(entry_price * (1 + config.DEFAULT_TAKE_PROFIT_PCT), 2)
        position = self.calculate_position_size(entry_price)
        
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        # Lower R/R requirement for BUY signals to get more opportunities
        if rr_ratio < 1.5:
            return None
        
        return {
            'action': 'BUY',
            'symbol': quote['symbol'],
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'shares': position['shares'],
            'total_cost': position['total_cost'],
            'risk_amount': position['risk_amount'],
            'risk_reward_ratio': round(rr_ratio, 2),
            'confidence': self._calculate_confidence(buy_signals, indicators),
            'signals': buy_signals,
            'reason': self._generate_reason(buy_signals, indicators)
        }
    
    def generate_sell_signal(self, quote: Dict, indicators: Dict) -> Optional[Dict]:
        """Generate sell signal"""
        signals = indicators.get('signals', {})
        sell_signals = signals.get('sell', [])
        
        # Also check for overbought conditions
        rsi = indicators.get('rsi', {})
        stoch = indicators.get('stochastic', {})
        
        if rsi.get('rsi', 50) > 70:
            sell_signals.append('RSI Overbought at ' + f"{rsi['rsi']:.1f}")
        if stoch.get('signal') == 'overbought':
            sell_signals.append('Stochastic Overbought')
        
        if len(sell_signals) < 1:
            return None
        
        current_price = quote.get('current_price', 0)
        if not current_price:
            return None
        
        entry_price = round(current_price * 1.005, 2)
        stop_loss = round(entry_price * (1 + config.DEFAULT_STOP_LOSS_PCT), 2)
        take_profit = round(entry_price * (1 - config.DEFAULT_TAKE_PROFIT_PCT), 2)
        
        risk = stop_loss - entry_price
        reward = entry_price - take_profit
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'action': 'SELL',
            'symbol': quote['symbol'],
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'current_price': current_price,
            'risk_reward_ratio': round(rr_ratio, 2),
            'confidence': self._calculate_sell_confidence(sell_signals, indicators),
            'signals': sell_signals,
            'reason': self._generate_sell_reason(sell_signals, indicators)
        }
    
    def _calculate_sell_confidence(self, signals: list, indicators: Dict) -> str:
        """Calculate sell trade confidence level"""
        score = len(signals) * 10
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi', 50) > 80:
            score += 25
        elif rsi.get('rsi', 50) > 70:
            score += 15
        return 'HIGH' if score >= 50 else 'MEDIUM' if score >= 30 else 'LOW'
    
    def _generate_sell_reason(self, signals: list, indicators: Dict) -> str:
        """Generate human-readable reason for sell trade"""
        reasons = []
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi', 50) > 70:
            reasons.append("RSI overbought at " + f"{rsi['rsi']:.1f}")
        stoch = indicators.get('stochastic', {})
        if stoch.get('signal') == 'overbought':
            reasons.append("Stochastic overbought")
        if signals:
            reasons.extend(signals[:2])
        return "; ".join(reasons) if reasons else "Multiple bearish signals"
    
    def _calculate_confidence(self, signals: list, indicators: Dict) -> str:
        """Calculate trade confidence level"""
        count = len(signals)
        rsi = indicators.get('rsi', {})
        macd = indicators.get('macd', {})
        
        score = count * 10
        
        if rsi.get('rsi', 50) < 25:
            score += 20
        elif rsi.get('rsi', 50) < 30:
            score += 15
        
        if macd.get('histogram', 0) > 0:
            score += 10
        
        if score >= 50:
            return 'HIGH'
        elif score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_reason(self, signals: list, indicators: Dict) -> str:
        """Generate human-readable reason for trade"""
        reasons = []
        
        rsi = indicators.get('rsi', {})
        if rsi.get('rsi', 50) < 30:
            reasons.append("RSI oversold at " + f"{rsi['rsi']:.1f}")
        
        macd = indicators.get('macd', {})
        if macd.get('trend') == 'bullish':
            reasons.append("MACD bullish crossover")
        
        stoch = indicators.get('stochastic', {})
        if stoch.get('signal') == 'oversold':
            reasons.append("Stochastic oversold")
        
        if signals:
            reasons.extend(signals[:2])
        
        return "; ".join(reasons) if reasons else "Multiple bullish signals"


def generate_trade_recommendation(quote: Dict, indicators: Dict) -> Optional[Dict]:
    """Generate complete trade recommendation"""
    generator = TradeSignalGenerator()
    
    buy_signal = generator.generate_buy_signal(quote, indicators)
    if buy_signal:
        return buy_signal
    
    sell_signal = generator.generate_sell_signal(quote, indicators)
    if sell_signal:
        return sell_signal
    
    return None