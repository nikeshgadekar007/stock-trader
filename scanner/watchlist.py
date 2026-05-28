"""
Stock Watchlist Manager
Track and monitor multiple stocks
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class Watchlist:
    """Stock watchlist manager"""
    
    def __init__(self, filepath: str = "data/watchlist.json"):
        self.filepath = filepath
        self.watchlist = self._load()
    
    def _load(self) -> List[Dict]:
        """Load watchlist from file"""
        try:
            if Path(self.filepath).exists():
                with open(self.filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading watchlist: {e}")
        return []
    
    def _save(self):
        """Save watchlist to file"""
        try:
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, 'w') as f:
                json.dump(self.watchlist, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving watchlist: {e}")
    
    def add(self, symbol: str, notes: str = "", alert_price: float = None, alert_type: str = None):
        """Add stock to watchlist"""
        # Check if already exists
        if any(s['symbol'].upper() == symbol.upper() for s in self.watchlist):
            return False
        
        self.watchlist.append({
            'symbol': symbol.upper(),
            'added_date': datetime.now().isoformat(),
            'notes': notes,
            'alert_price': alert_price,
            'alert_type': alert_type,  # 'above' or 'below'
            'last_checked': None,
            'last_price': None
        })
        self._save()
        return True
    
    def remove(self, symbol: str) -> bool:
        """Remove stock from watchlist"""
        initial_len = len(self.watchlist)
        self.watchlist = [s for s in self.watchlist if s['symbol'].upper() != symbol.upper()]
        if len(self.watchlist) < initial_len:
            self._save()
            return True
        return False
    
    def update(self, symbol: str, **kwargs):
        """Update stock in watchlist"""
        for stock in self.watchlist:
            if stock['symbol'].upper() == symbol.upper():
                stock.update(kwargs)
                self._save()
                return True
        return False
    
    def get(self, symbol: str = None) -> Optional[Dict]:
        """Get stock from watchlist"""
        if symbol:
            for stock in self.watchlist:
                if stock['symbol'].upper() == symbol.upper():
                    return stock
            return None
        return self.watchlist
    
    def set_alert(self, symbol: str, price: float, alert_type: str):
        """Set price alert for stock"""
        return self.update(symbol, alert_price=price, alert_type=alert_type)
    
    def check_alerts(self, prices: Dict[str, float]) -> List[Dict]:
        """Check which alerts have been triggered"""
        triggered = []
        for stock in self.watchlist:
            if stock.get('alert_price') and stock.get('alert_type'):
                symbol = stock['symbol']
                if symbol in prices:
                    current_price = prices[symbol]
                    alert_price = stock['alert_price']
                    alert_type = stock['alert_type']
                    
                    if alert_type == 'above' and current_price >= alert_price:
                        triggered.append({
                            'symbol': symbol,
                            'type': 'above',
                            'alert_price': alert_price,
                            'current_price': current_price,
                            'message': f"{symbol} is above ${alert_price} (now ${current_price})"
                        })
                    elif alert_type == 'below' and current_price <= alert_price:
                        triggered.append({
                            'symbol': symbol,
                            'type': 'below',
                            'alert_price': alert_price,
                            'current_price': current_price,
                            'message': f"{symbol} is below ${alert_price} (now ${current_price})"
                        })
        return triggered
    
    def get_watchlist(self) -> List[Dict]:
        """Get all stocks in watchlist"""
        return self.watchlist
    
    def clear(self):
        """Clear entire watchlist"""
        self.watchlist = []
        self._save()

def get_default_watchlist() -> List[str]:
    """Get default watchlist symbols"""
    return [
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS',
        # Healthcare
        'JNJ', 'PFE', 'UNH',
        # Energy
        'XOM', 'CVX',
        # Consumer
        'WMT', 'KO', 'PG'
    ]

if __name__ == "__main__":
    # Test
    wl = Watchlist()
    
    # Add default stocks
    for symbol in get_default_watchlist():
        wl.add(symbol)
    
    print(f"Watchlist has {len(wl.get_watchlist())} stocks")
    print("Symbols:", [s['symbol'] for s in wl.get_watchlist()[:5]], "...")