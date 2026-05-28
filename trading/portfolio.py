"""
Portfolio Tracker
Track your trades and portfolio performance
"""

import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class Trade:
    """Individual trade record"""
    def __init__(self, symbol: str, action: str, quantity: int, price: float, 
                 date: str = None, commission: float = 0):
        self.symbol = symbol.upper()
        self.action = action.upper()  # 'BUY' or 'SELL'
        self.quantity = quantity
        self.price = price
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.commission = commission
        self.total_cost = (quantity * price) + commission
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'action': self.action,
            'quantity': self.quantity,
            'price': self.price,
            'date': self.date,
            'commission': self.commission,
            'total_cost': self.total_cost
        }

class Portfolio:
    """Portfolio tracker"""
    
    def __init__(self, filepath: str = "data/portfolio.json"):
        self.filepath = filepath
        self.trades = self._load()
        self.positions = self._calculate_positions()
    
    def _load(self) -> List[Dict]:
        """Load trades from file"""
        try:
            if Path(self.filepath).exists():
                with open(self.filepath, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading portfolio: {e}")
        return []
    
    def _save(self):
        """Save trades to file"""
        try:
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, 'w') as f:
                json.dump(self.trades, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
    
    def _calculate_positions(self) -> Dict[str, Dict]:
        """Calculate current positions from trades"""
        positions = {}
        
        for trade in self.trades:
            symbol = trade['symbol']
            action = trade['action']
            quantity = trade['quantity']
            price = trade['price']
            
            if symbol not in positions:
                positions[symbol] = {'quantity': 0, 'avg_cost': 0, 'total_cost': 0}
            
            if action == 'BUY':
                old_qty = positions[symbol]['quantity']
                old_cost = positions[symbol]['total_cost']
                new_cost = old_cost + (quantity * price)
                new_qty = old_qty + quantity
                positions[symbol]['quantity'] = new_qty
                positions[symbol]['avg_cost'] = new_cost / new_qty if new_qty > 0 else 0
                positions[symbol]['total_cost'] = new_cost
            elif action == 'SELL':
                positions[symbol]['quantity'] -= quantity
                if positions[symbol]['quantity'] <= 0:
                    positions[symbol] = {'quantity': 0, 'avg_cost': 0, 'total_cost': 0}
        
        # Remove empty positions
        return {k: v for k, v in positions.items() if v['quantity'] > 0}
    
    def add_trade(self, symbol: str, action: str, quantity: int, price: float, 
                  date: str = None, commission: float = 0):
        """Add a trade"""
        trade = Trade(symbol, action, quantity, price, date, commission)
        self.trades.append(trade.to_dict())
        self._save()
        self.positions = self._calculate_positions()
        return True
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get current positions"""
        return self.positions
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a symbol"""
        return self.positions.get(symbol.upper())
    
    def get_trades(self, symbol: str = None) -> List[Dict]:
        """Get trade history"""
        if symbol:
            return [t for t in self.trades if t['symbol'].upper() == symbol.upper()]
        return self.trades
    
    def calculate_pnl(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Calculate profit/loss for all positions"""
        pnl_list = []
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                quantity = position['quantity']
                avg_cost = position['avg_cost']
                
                market_value = quantity * current_price
                cost_basis = quantity * avg_cost
                pnl = market_value - cost_basis
                pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
                
                pnl_list.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'market_value': market_value,
                    'cost_basis': cost_basis,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                })
        
        return sorted(pnl_list, key=lambda x: x['pnl'], reverse=True)
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """Get total portfolio value"""
        total = 0
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total += position['quantity'] * current_prices[symbol]
        return total
    
    def get_total_pnl(self, current_prices: Dict[str, float]) -> Dict:
        """Get total P&L"""
        pnl_list = self.calculate_pnl(current_prices)
        
        total_cost = sum(p['cost_basis'] for p in pnl_list)
        total_value = sum(p['market_value'] for p in pnl_list)
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_cost': total_cost,
            'total_value': total_value,
            'total_pnl': total_pnl,
            'total_pnl_percent': total_pnl_percent,
            'positions': pnl_list
        }
    
    def get_performance_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Get performance summary"""
        pnl = self.get_total_pnl(current_prices)
        
        winning_positions = [p for p in pnl['positions'] if p['pnl'] > 0]
        losing_positions = [p for p in pnl['positions'] if p['pnl'] < 0]
        
        return {
            'total_value': pnl['total_value'],
            'total_cost': pnl['total_cost'],
            'total_pnl': pnl['total_pnl'],
            'total_pnl_percent': pnl['total_pnl_percent'],
            'num_positions': len(pnl['positions']),
            'winning_positions': len(winning_positions),
            'losing_positions': len(losing_positions),
            'win_rate': len(winning_positions) / len(pnl['positions']) if pnl['positions'] else 0
        }

if __name__ == "__main__":
    # Test
    portfolio = Portfolio()
    
    # Add some test trades
    portfolio.add_trade('AAPL', 'BUY', 100, 150.00)
    portfolio.add_trade('AAPL', 'BUY', 50, 155.00)
    portfolio.add_trade('MSFT', 'BUY', 50, 350.00)
    
    # Get positions
    print("Current Positions:")
    for symbol, pos in portfolio.get_positions().items():
        print(f"  {symbol}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
    
    # Calculate P&L
    current_prices = {'AAPL': 175.00, 'MSFT': 380.00}
    pnl = portfolio.get_total_pnl(current_prices)
    print(f"\nTotal P&L: ${pnl['total_pnl']:.2f} ({pnl['total_pnl_percent']:.2f}%)")