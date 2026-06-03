"""
IBKR Trader - Automated Trading with Interactive Brokers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ib_insync import IB, Stock, MarketOrder, LimitOrder, StopOrder, BracketOrder
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False

class IBKRTrader:
    """Interactive Brokers Trader"""
    
    def __init__(self, host='127.0.0.1', port=7496, client_id=1):
        """
        Initialize IBKR Trader
        
        Args:
            host: IB Gateway/TWS host (default: localhost)
            port: Port (7496=paper, 7497=live)
            client_id: Unique client ID
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.connected = False
        
    def connect(self):
        """Connect to IBKR"""
        if not IBKR_AVAILABLE:
            return {'success': False, 'error': 'ib_insync not installed. Run: pip install ib_insync'}
        
        try:
            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            return {'success': True, 'message': 'Connected to IBKR'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib:
            self.ib.disconnect()
            self.connected = False
    
    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            return {'error': 'Not connected'}
        
        account = self.ib.accountSummary()
        cash = next((a for a in account if a.tag == 'NetLiquidation'), None)
        buying_power = next((a for a in account if a.tag == 'BuyingPower'), None)
        
        return {
            'cash': float(cash.value) if cash else 0,
            'buying_power': float(buying_power.value) if buying_power else 0
        }
    
    def place_order(self, symbol, action, quantity, order_type='LMT', price=None):
        """
        Place a single order
        
        Args:
            symbol: Stock symbol (e.g., 'TSLA')
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            order_type: 'MKT', 'LMT', 'STP'
            price: Limit price (required for LMT orders)
        """
        if not self.connected:
            return {'error': 'Not connected'}
        
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            
            if order_type == 'MKT':
                order = MarketOrder(action, quantity)
            elif order_type == 'LMT' and price:
                order = LimitOrder(action, quantity, price)
            elif order_type == 'STP' and price:
                order = StopOrder(action, quantity, price)
            else:
                return {'error': 'Invalid order type or missing price'}
            
            trade = self.ib.placeOrder(contract, order)
            
            return {
                'success': True,
                'order_id': trade.order.orderId,
                'status': 'Submitted',
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def place_bracket_order(self, symbol, action, quantity, entry_price, stop_price, target_price):
        """
        Place a bracket order (entry + stop loss + take profit)
        
        Args:
            symbol: Stock symbol
            action: 'BUY' or 'SELL'
            quantity: Number of shares
            entry_price: Entry limit price
            stop_price: Stop loss price
            target_price: Take profit price
        """
        if not self.connected:
            return {'error': 'Not connected'}
        
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Create bracket order
            parent = LimitOrder(action, quantity, entry_price)
            
            if action == 'BUY':
                stop = StopOrder('SELL', quantity, stop_price, tif='GTC')
                target = LimitOrder('SELL', quantity, target_price, tif='GTC')
            else:
                stop = StopOrder('BUY', quantity, stop_price, tif='GTC')
                target = LimitOrder('BUY', quantity, target_price, tif='GTC')
            
            bracket = BracketOrder(parent, stop, target)
            
            # Place orders
            trades = []
            for order in bracket:
                trade = self.ib.placeOrder(contract, order)
                trades.append({
                    'order_id': trade.order.orderId,
                    'type': order.orderType,
                    'action': order.action,
                    'quantity': order.totalQuantity,
                    'price': order.lmtPrice if hasattr(order, 'lmtPrice') else order.auxPrice
                })
            
            return {
                'success': True,
                'trades': trades,
                'message': f'Bracket order placed: {action} {quantity} {symbol} @ ${entry_price}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_positions(self):
        """Get current positions"""
        if not self.connected:
            return []
        
        positions = []
        for pos in self.ib.positions():
            if pos.contract.symbol:
                positions.append({
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost / pos.position if pos.position != 0 else 0,
                    'market_value': pos.marketValue
                })
        return positions
    
    def get_pending_orders(self):
        """Get pending orders"""
        if not self.connected:
            return []
        
        orders = []
        for trade in self.ib.trades():
            if trade.orderStatus.status == 'Submitted':
                orders.append({
                    'order_id': trade.order.orderId,
                    'symbol': trade.contract.symbol,
                    'action': trade.order.action,
                    'quantity': trade.order.totalQuantity,
                    'order_type': trade.order.orderType,
                    'price': trade.order.lmtPrice if hasattr(trade.order, 'lmtPrice') else None
                })
        return orders
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        if not self.connected:
            return {'error': 'Not connected'}
        
        try:
            for trade in self.ib.trades():
                if trade.order.orderId == order_id:
                    self.ib.cancelOrder(trade.order)
                    return {'success': True, 'message': f'Order {order_id} cancelled'}
            return {'success': False, 'error': 'Order not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Demo function for testing without IBKR
def demo_trade(signal):
    """Demo trade without connecting to IBKR"""
    return {
        'success': True,
        'mode': 'DEMO',
        'trade': {
            'symbol': signal.get('symbol', 'AAPL'),
            'action': signal.get('action', 'BUY'),
            'quantity': signal.get('shares', 10),
            'entry': signal.get('entry', 150.00),
            'stop': signal.get('stop', 147.00),
            'target': signal.get('target', 156.00)
        },
        'message': 'This is a DEMO trade. Connect IBKR for real trading.'
    }


if __name__ == '__main__':
    # Test connection
    trader = IBKRTrader()
    result = trader.connect()
    print(result)
    
    if result.get('success'):
        print(trader.get_account_info())
        trader.disconnect()