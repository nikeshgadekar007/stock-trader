"""
Paper Trading Module
Simulated trading with Alpaca API or local simulation
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import config

class PaperTrader:
    """Paper trading simulator"""
    
    def __init__(self, initial_capital: float = None):
        self.initial_capital = initial_capital or config.CAPITAL
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.trade_id = 0
        
        # Load existing trades if any
        self._load_trades()
    
    def _load_trades(self):
        """Load trades from file"""
        trades_file = f"{config.OUTPUT_DIR}/paper_trades.json"
        if os.path.exists(trades_file):
            try:
                with open(trades_file, 'r') as f:
                    data = json.load(f)
                    self.cash = data.get('cash', self.initial_capital)
                    self.positions = data.get('positions', {})
                    self.trades = data.get('trades', [])
            except:
                pass
    
    def _save_trades(self):
        """Save trades to file"""
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        trades_file = f"{config.OUTPUT_DIR}/paper_trades.json"
        with open(trades_file, 'w') as f:
            json.dump({
                'cash': self.cash,
                'positions': self.positions,
                'trades': self.trades,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def buy(self, symbol: str, quantity: int, price: float) -> Dict:
        """Execute a BUY order"""
        cost = quantity * price
        commission = max(0.01 * cost, 1)  # $1 or 1% commission
        
        if cost + commission > self.cash:
            return {'success': False, 'error': 'Insufficient funds'}
        
        self.cash -= (cost + commission)
        self.trade_id += 1
        
        if symbol in self.positions:
            old_qty = self.positions[symbol]['quantity']
            old_cost = self.positions[symbol]['avg_cost'] * old_qty
            new_qty = old_qty + quantity
            new_cost = (old_cost + cost) / new_qty
            self.positions[symbol] = {
                'quantity': new_qty,
                'avg_cost': new_cost
            }
        else:
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_cost': price
            }
        
        trade = {
            'id': self.trade_id,
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'total': cost + commission,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)
        self._save_trades()
        
        return {'success': True, 'trade': trade}
    
    def sell(self, symbol: str, quantity: int, price: float) -> Dict:
        """Execute a SELL order"""
        if symbol not in self.positions:
            return {'success': False, 'error': 'No position to sell'}
        
        if self.positions[symbol]['quantity'] < quantity:
            return {'success': False, 'error': 'Insufficient shares'}
        
        proceeds = quantity * price
        commission = max(0.01 * proceeds, 1)
        avg_cost = self.positions[symbol]['avg_cost']
        pnl = (price - avg_cost) * quantity - commission
        
        self.cash += (proceeds - commission)
        self.trade_id += 1
        
        self.positions[symbol]['quantity'] -= quantity
        if self.positions[symbol]['quantity'] == 0:
            del self.positions[symbol]
        
        trade = {
            'id': self.trade_id,
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'total': proceeds - commission,
            'pnl': pnl,
            'timestamp': datetime.now().isoformat()
        }
        self.trades.append(trade)
        self._save_trades()
        
        return {'success': True, 'trade': trade}
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        positions_value = 0
        for symbol, pos in self.positions.items():
            price = current_prices.get(symbol, pos['avg_cost'])
            positions_value += pos['quantity'] * price
        return self.cash + positions_value
    
    def get_positions(self) -> Dict:
        """Get current positions"""
        return self.positions.copy()
    
    def get_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades"""
        return self.trades[-limit:]
    
    def get_performance(self) -> Dict:
        """Calculate performance metrics"""
        total_value = self.get_portfolio_value({})
        pnl = total_value - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        
        winning_trades = [t for t in self.trades if t.get('action') == 'SELL' and t.get('pnl', 0) > 0]
        losing_trades = [t for t in self.trades if t.get('action') == 'SELL' and t.get('pnl', 0) < 0]
        
        total_trades = len([t for t in self.trades if t.get('action') == 'SELL'])
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash': self.cash,
            'pnl': pnl,
            'pnl_percent': pnl_pct,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'open_positions': len(self.positions)
        }
    
    def reset(self):
        """Reset paper trading account"""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.trade_id = 0
        self._save_trades()
        print(f"Paper trading account reset. Capital: ${self.initial_capital:,.2f}")


class AlpacaPaperTrader:
    """Alpaca API paper trading (requires API keys)"""
    
    def __init__(self):
        self.api_key = config.ALPACA_API_KEY
        self.api_secret = config.ALPACA_API_SECRET
        self.base_url = config.ALPACA_PAPER_URL
        self.enabled = bool(self.api_key and self.api_secret)
        
        if self.enabled:
            self._init_alpaca()
        else:
            print("Alpaca API not configured. Using local paper trader.")
            self.local_trader = PaperTrader()
    
    def _init_alpaca(self):
        """Initialize Alpaca API connection"""
        try:
            import alpaca_trade_api as tradeapi
            self.api = tradeapi.REST(self.api_key, self.api_secret, self.base_url)
            print("Alpaca API connected!")
        except ImportError:
            print("Alpaca SDK not installed. Run: pip install alpaca-trade-api")
            self.enabled = False
            self.local_trader = PaperTrader()
    
    def buy(self, symbol: str, quantity: int, price: float = None) -> Dict:
        """Buy via Alpaca API"""
        if not self.enabled:
            return self.local_trader.buy(symbol, quantity, price or 0)
        
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='day'
            )
            return {'success': True, 'message': 'Order submitted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sell(self, symbol: str, quantity: int, price: float = None) -> Dict:
        """Sell via Alpaca API"""
        if not self.enabled:
            return self.local_trader.sell(symbol, quantity, price or 0)
        
        try:
            self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='day'
            )
            return {'success': True, 'message': 'Order submitted'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_positions(self) -> List[Dict]:
        """Get positions from Alpaca"""
        if not self.enabled:
            return self.local_trader.get_positions()
        
        try:
            positions = self.api.list_positions()
            return {p.symbol: {'quantity': int(p.qty), 'avg_cost': float(p.avg_entry_price)} for p in positions}
        except Exception as e:
            print(f"Error getting positions: {e}")
            return self.local_trader.get_positions()
    
    def get_performance(self) -> Dict:
        """Get performance from Alpaca"""
        if not self.enabled:
            return self.local_trader.get_performance()
        
        try:
            account = self.api.get_account()
            return {
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'pnl': float(account.equity) - float(account.last_equity)
            }
        except Exception as e:
            print(f"Error getting performance: {e}")
            return self.local_trader.get_performance()
