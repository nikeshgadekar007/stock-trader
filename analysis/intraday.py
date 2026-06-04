"""
Intraday Trading Analysis
Specialized indicators and analysis for day trading
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, time

def get_market_session() -> str:
    """Get current market session - handles any timezone"""
    from datetime import timezone, timedelta
    
    # Get current time in UTC
    utc = timezone.utc
    now_utc = datetime.now(utc)
    
    # Convert to EST (UTC-5) or EDT (UTC-4) depending on DST
    # US markets: EST (UTC-5) Nov-Mar, EDT (UTC-4) Mar-Nov
    # Simple DST check: March to November = EDT
    month = now_utc.month
    
    # Determine if DST is active (US DST: second Sunday March to first Sunday November)
    # For simplicity, use EDT (UTC-4) from March to November
    if month >= 3 and month <= 10:
        est_offset = timedelta(hours=-4)  # EDT
    else:
        est_offset = timedelta(hours=-5)  # EST
    
    est = timezone(est_offset)
    now_est = now_utc.astimezone(est)
    current_time = now_est.time()
    current_date = now_est.date()
    
    # Check if weekend
    weekday = current_date.weekday()
    if weekday >= 5:  # Saturday or Sunday
        return "CLOSED"
    
    # Market hours in EST/EDT
    market_open = time(9, 30)
    market_close = time(16, 0)
    pre_market_open = time(4, 0)
    pre_market_close = time(9, 30)
    after_hours_open = time(16, 0)
    after_hours_close = time(20, 0)
    
    if pre_market_open <= current_time < pre_market_close:
        return "PRE_MARKET"
    elif market_open <= current_time < market_close:
        return "REGULAR_MARKET"
    elif after_hours_open <= current_time <= after_hours_close:
        return "AFTER_HOURS"
    else:
        return "CLOSED"

def calculate_vwap(df: pd.DataFrame) -> float:
    """Calculate Volume Weighted Average Price (VWAP)"""
    if len(df) < 2 or 'volume' not in df.columns:
        return 0
    
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    
    vwap = cumulative_tp_vol / cumulative_vol
    return float(vwap.iloc[-1])

def calculate_vwap_levels(df: pd.DataFrame, std_multiplier: float = 1.0) -> Dict:
    """Calculate VWAP with standard deviation bands"""
    if len(df) < 20 or 'volume' not in df.columns:
        return {}
    
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    cumulative_tp_vol = (typical_price * df['volume']).cumsum()
    cumulative_vol = df['volume'].cumsum()
    
    vwap = cumulative_tp_vol / cumulative_vol
    rolling_std = typical_price.rolling(window=20).std()
    std = rolling_std.iloc[-1] if not pd.isna(rolling_std.iloc[-1]) else 0
    current_price = df['close'].iloc[-1]
    
    return {
        'vwap': float(vwap.iloc[-1]),
        'upper_band': float(vwap.iloc[-1] + std_multiplier * std),
        'lower_band': float(vwap.iloc[-1] - std_multiplier * std),
        'position': 'above' if current_price > vwap.iloc[-1] else 'below',
        'distance_percent': ((current_price - vwap.iloc[-1]) / vwap.iloc[-1] * 100) if vwap.iloc[-1] > 0 else 0
    }

def calculate_momentum(df: pd.DataFrame, periods: List[int] = [5, 10, 20]) -> Dict:
    """Calculate price momentum across multiple timeframes"""
    momentum = {}
    current_price = df['close'].iloc[-1]
    
    for period in periods:
        if len(df) >= period:
            past_price = df['close'].iloc[-period]
            mom = ((current_price - past_price) / past_price * 100) if past_price > 0 else 0
            momentum[f'momentum_{period}'] = mom
    
    return momentum

def calculate_intraday_strength(df: pd.DataFrame) -> Dict:
    """Calculate intraday strength indicators"""
    if len(df) < 5:
        return {}
    
    current_price = df['close'].iloc[-1]
    open_price = df['open'].iloc[0] if 'open' in df.columns else current_price
    day_high = df['high'].max()
    day_low = df['low'].min()
    day_range = day_high - day_low
    
    if day_range > 0:
        range_position = ((current_price - day_low) / day_range) * 100
    else:
        range_position = 50
    
    open_close_diff = ((current_price - open_price) / open_price * 100) if open_price > 0 else 0
    recent_returns = df['close'].pct_change().tail(10)
    volatility = recent_returns.std() * 100 if len(recent_returns) > 1 else 0
    
    sma_5 = df['close'].rolling(5).mean().iloc[-1] if len(df) >= 5 else current_price
    sma_10 = df['close'].rolling(10).mean().iloc[-1] if len(df) >= 10 else current_price
    
    if current_price > sma_5 > sma_10:
        trend = "STRONG_BULLISH"
    elif current_price > sma_5:
        trend = "BULLISH"
    elif current_price < sma_5 < sma_10:
        trend = "STRONG_BEARISH"
    elif current_price < sma_5:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    
    return {
        'range_position': range_position,
        'open_close_diff': open_close_diff,
        'volatility': volatility,
        'trend': trend,
        'sma_5': sma_5,
        'sma_10': sma_10
    }

def calculate_support_resistance_levels(df: pd.DataFrame, lookback: int = 50) -> Dict:
    """Find key support and resistance levels"""
    if len(df) < lookback:
        lookback = len(df)
    
    recent = df.tail(lookback)
    highs = recent['high'].values
    lows = recent['low'].values
    resistance = float(highs.max())
    support = float(lows.min())
    current_price = df['close'].iloc[-1]
    
    return {
        'resistance': resistance,
        'support': support,
        'resistance_distance': ((current_price - resistance) / resistance * 100) if resistance > 0 else 0,
        'support_distance': ((current_price - support) / support * 100) if support > 0 else 0
    }

def get_intraday_signal(df: pd.DataFrame) -> Dict:
    """Generate comprehensive intraday trading signal"""
    if len(df) < 20:
        return {'signal': 'INSUFFICIENT_DATA', 'confidence': 0, 'details': {}}
    
    signals = []
    confidence_scores = []
    
    vwap_data = calculate_vwap_levels(df)
    if vwap_data:
        if vwap_data['position'] == 'above':
            signals.append('ABOVE_VWAP')
            confidence_scores.append(0.7)
        else:
            signals.append('BELOW_VWAP')
            confidence_scores.append(0.7)
    
    strength = calculate_intraday_strength(df)
    if strength:
        if strength['trend'] in ['STRONG_BULLISH', 'BULLISH']:
            signals.append('BULLISH_TREND')
            confidence_scores.append(0.8)
        elif strength['trend'] in ['STRONG_BEARISH', 'BEARISH']:
            signals.append('BEARISH_TREND')
            confidence_scores.append(0.8)
        
        if strength['range_position'] > 70:
            signals.append('NEAR_RESISTANCE')
            confidence_scores.append(0.6)
        elif strength['range_position'] < 30:
            signals.append('NEAR_SUPPORT')
            confidence_scores.append(0.6)
    
    momentum = calculate_momentum(df)
    if momentum:
        if momentum.get('momentum_5', 0) > 0.5:
            signals.append('POSITIVE_MOMENTUM')
            confidence_scores.append(0.6)
        elif momentum.get('momentum_5', 0) < -0.5:
            signals.append('NEGATIVE_MOMENTUM')
            confidence_scores.append(0.6)
    
    bullish_signals = sum(1 for s in signals if 'BULLISH' in s or 'ABOVE' in s or 'SUPPORT' in s or 'POSITIVE' in s)
    bearish_signals = sum(1 for s in signals if 'BEARISH' in s or 'BELOW' in s or 'RESISTANCE' in s or 'NEGATIVE' in s)
    
    total = bullish_signals + bearish_signals
    if total == 0:
        return {'signal': 'HOLD', 'confidence': 0.5, 'details': {'signals': signals}}
    
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
    
    if bullish_signals > bearish_signals:
        return {
            'signal': 'BUY',
            'confidence': avg_confidence,
            'details': {'signals': signals, 'bullish': bullish_signals, 'bearish': bearish_signals}
        }
    elif bearish_signals > bullish_signals:
        return {
            'signal': 'SELL',
            'confidence': avg_confidence,
            'details': {'signals': signals, 'bullish': bullish_signals, 'bearish': bearish_signals}
        }
    else:
        return {'signal': 'HOLD', 'confidence': 0.5, 'details': {'signals': signals}}
