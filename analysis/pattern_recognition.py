"""
Chart Pattern Recognition for Stock Trading
Detects common technical patterns like head and shoulders, double top, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Pattern:
    """Detected chart pattern"""
    name: str
    direction: str  # 'bullish' or 'bearish'
    confidence: float  # 0-100%
    description: str
    points: List[Tuple[int, float]]  # (index, price) points forming the pattern

def detect_double_top(df: pd.DataFrame, window: int = 20) -> Optional[Pattern]:
    """Detect double top pattern"""
    if len(df) < window * 2:
        return None
    
    highs = df['high'].values
    recent_highs = highs[-window*2:]
    
    # Find local maxima
    peaks = []
    for i in range(1, len(recent_highs)-1):
        if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i+1]:
            peaks.append((i, recent_highs[i]))
    
    if len(peaks) < 2:
        return None
    
    # Check for two similar peaks
    peaks.sort(key=lambda x: x[1], reverse=True)
    top1, top2 = peaks[0], peaks[1]
    
    # Peaks should be within 5% of each other
    if abs(top1[1] - top2[1]) / top1[1] < 0.05:
        # Check if there's a valley between them
        valley_start = min(top1[0], top2[0])
        valley_end = max(top1[0], top2[0])
        valley = min(recent_highs[valley_start:valley_end])
        
        # Valley should be at least 5% below peaks
        if (top1[1] - valley) / top1[1] > 0.05:
            return Pattern(
                name='Double Top',
                direction='bearish',
                confidence=75.0,
                description='Bearish reversal pattern - two peaks at similar levels',
                points=[(len(highs)-len(recent_highs)+top1[0], top1[1]),
                         (len(highs)-len(recent_highs)+top2[0], top2[1])]
            )
    
    return None

def detect_double_bottom(df: pd.DataFrame, window: int = 20) -> Optional[Pattern]:
    """Detect double bottom pattern"""
    if len(df) < window * 2:
        return None
    
    lows = df['low'].values
    recent_lows = lows[-window*2:]
    
    # Find local minima
    bottoms = []
    for i in range(1, len(recent_lows)-1):
        if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i+1]:
            bottoms.append((i, recent_lows[i]))
    
    if len(bottoms) < 2:
        return None
    
    # Check for two similar bottoms
    bottoms.sort(key=lambda x: x[1])
    bot1, bot2 = bottoms[0], bottoms[1]
    
    # Bottoms should be within 5% of each other
    if abs(bot1[1] - bot2[1]) / bot1[1] < 0.05:
        # Check if there's a peak between them
        peak_start = min(bot1[0], bot2[0])
        peak_end = max(bot1[0], bot2[0])
        peak = max(recent_lows[peak_start:peak_end])
        
        # Peak should be at least 5% above bottoms
        if (peak - bot1[1]) / bot1[1] > 0.05:
            return Pattern(
                name='Double Bottom',
                direction='bullish',
                confidence=75.0,
                description='Bullish reversal pattern - two bottoms at similar levels',
                points=[(len(lows)-len(recent_lows)+bot1[0], bot1[1]),
                         (len(lows)-len(recent_lows)+bot2[0], bot2[1])]
            )
    
    return None

def detect_head_and_shoulders(df: pd.DataFrame, window: int = 60) -> Optional[Pattern]:
    """Detect head and shoulders pattern"""
    if len(df) < window:
        return None
    
    highs = df['high'].values[-window:]
    
    # Find peaks
    peaks = []
    for i in range(2, len(highs)-2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            peaks.append((i, highs[i]))
    
    if len(peaks) < 3:
        return None
    
    # Sort by price to find head (highest) and shoulders
    peaks.sort(key=lambda x: x[1], reverse=True)
    
    # Head should be highest
    head = peaks[0]
    
    # Shoulders should be similar height (within 10%)
    shoulders = [p for p in peaks[1:] if abs(p[1] - head[1]) / head[1] < 0.10]
    
    if len(shoulders) >= 2:
        # Check if shoulders are on either side of head
        left_shoulder = min(shoulders, key=lambda x: x[0])
        right_shoulder = max(shoulders, key=lambda x: x[0])
        
        if left_shoulder[0] < head[0] < right_shoulder[0]:
            return Pattern(
                name='Head and Shoulders',
                direction='bearish',
                confidence=70.0,
                description='Bearish reversal pattern - head with shoulders on both sides',
                points=[(len(highs)-window+left_shoulder[0], left_shoulder[1]),
                         (len(highs)-window+head[0], head[1]),
                         (len(highs)-window+right_shoulder[0], right_shoulder[1])]
            )
    
    return None

def detect_ascending_triangle(df: pd.DataFrame, window: int = 30) -> Optional[Pattern]:
    """Detect ascending triangle pattern"""
    if len(df) < window:
        return None
    
    recent = df[-window:]
    
    # Find resistance level (horizontal top)
    resistance = recent['high'].max()
    resistance_count = sum(1 for h in recent['high'] if abs(h - resistance) / resistance < 0.02)
    
    if resistance_count < 2:
        return None
    
    # Find higher lows
    lows = recent['low'].values
    higher_lows = 0
    for i in range(2, len(lows)):
        if lows[i] > lows[i-2]:
            higher_lows += 1
    
    if higher_lows >= 3:
        return Pattern(
            name='Ascending Triangle',
            direction='bullish',
            confidence=70.0,
            description='Bullish continuation - flat resistance with rising lows',
            points=[(len(df)-window, resistance), (len(df)-1, lows[-1])]
        )
    
    return None

def detect_descending_triangle(df: pd.DataFrame, window: int = 30) -> Optional[Pattern]:
    """Detect descending triangle pattern"""
    if len(df) < window:
        return None
    
    recent = df[-window:]
    
    # Find support level (horizontal bottom)
    support = recent['low'].min()
    support_count = sum(1 for l in recent['low'] if abs(l - support) / support < 0.02)
    
    if support_count < 2:
        return None
    
    # Find lower highs
    highs = recent['high'].values
    lower_highs = 0
    for i in range(2, len(highs)):
        if highs[i] < highs[i-2]:
            lower_highs += 1
    
    if lower_highs >= 3:
        return Pattern(
            name='Descending Triangle',
            direction='bearish',
            confidence=70.0,
            description='Bearish continuation - flat support with falling highs',
            points=[(len(df)-window, support), (len(df)-1, highs[-1])]
        )
    
    return None

def detect_support_resistance(df: pd.DataFrame, window: int = 50) -> Dict:
    """Detect key support and resistance levels"""
    if len(df) < window:
        return {'support': [], 'resistance': []}