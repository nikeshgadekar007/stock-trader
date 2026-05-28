"""
Stock Scanner and Filters
Filters stocks based on criteria and ranks them
"""

import pandas as pd
from typing import Dict, List
import config


class StockScanner:
    """Scans and filters stocks based on criteria"""
    
    def __init__(self):
        self.watchlist = config.DEFAULT_WATCHLIST
        
    def filter_by_price(self, quote: Dict) -> bool:
        """Filter by price range"""
        price = quote.get('current_price', 0)
        if price is None or price == 0:
            return False
        return config.MIN_PRICE <= price <= config.MAX_PRICE
    
    def filter_by_volume(self, quote: Dict) -> bool:
        """Filter by volume (liquidity)"""
        volume = quote.get('volume', 0)
        if volume is None:
            return False
        return volume >= config.MIN_VOLUME
    
    def filter_by_market_cap(self, fundamentals: Dict) -> bool:
        """Filter by market cap"""
        mcap = fundamentals.get('market_cap', 0)
        if mcap is None:
            return True
        return mcap <= config.MAX_MARKET_CAP
    
    def filter_by_price_change(self, quote: Dict) -> bool:
        """Filter by today's price change"""
        current = quote.get('current_price', 0)
        previous = quote.get('previous_close', 0)
        if current is None or previous is None or previous == 0:
            return True
        
        change_pct = ((current - previous) / previous) * 100
        return config.MIN_PRICE_CHANGE_PCT <= abs(change_pct) <= config.MAX_PRICE_CHANGE_PCT
    
    def filter_stock(self, quote: Dict, fundamentals: Dict = None) -> bool:
        """Apply all filters"""
        if not self.filter_by_price(quote):
            return False
        if not self.filter_by_volume(quote):
            return False
        if fundamentals and not self.filter_by_market_cap(fundamentals):
            return False
        if not self.filter_by_price_change(quote):
            return False
        return True
    
    def get_momentum_score(self, quote: Dict, history: pd.DataFrame = None) -> float:
        """Calculate momentum score (0-100)"""
        score = 0.0
        
        current = quote.get('current_price', 0)
        previous = quote.get('previous_close', 0)
        if current and previous and previous > 0:
            daily_return = ((current - previous) / previous) * 100
            if daily_return > 5:
                score += 30
            elif daily_return > 2:
                score += 20
            elif daily_return > 0:
                score += 10
        
        volume = quote.get('volume', 0)
        avg_volume = quote.get('avg_volume', 0)
        if volume and avg_volume and avg_volume > 0:
            vol_ratio = volume / avg_volume
            if vol_ratio > 2:
                score += 25
            elif vol_ratio > 1.5:
                score += 15
        
        return max(0, min(100, score))
    
    def rank_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """Rank stocks by multiple criteria"""
        ranked = []
        
        for stock in stocks:
            score = 0
            score += stock.get('momentum_score', 0) * 0.3
            score += stock.get('technical_score', 0) * 0.4
            score += stock.get('fundamental_score', 0) * 0.2
            score += stock.get('pattern_score', 0) * 0.1
            
            stock['composite_score'] = round(score, 2)
            ranked.append(stock)
        
        ranked.sort(key=lambda x: x['composite_score'], reverse=True)
        return ranked


def scan_stocks(quotes: List[Dict], fundamentals: Dict = None) -> List[Dict]:
    """Scan and filter stocks"""
    scanner = StockScanner()
    filtered = []
    
    for quote in quotes:
        if scanner.filter_stock(quote, fundamentals.get(quote['symbol']) if fundamentals else None):
            filtered.append(quote)
    
    return filtered