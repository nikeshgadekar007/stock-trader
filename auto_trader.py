"""
Automated Trading System
Runs continuously to monitor market and execute trades
"""

import time
import json
import threading
from datetime import datetime, time as dt_time
from typing import Dict, List
import config
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer, analyze_stock
from analysis.intraday import get_intraday_signal, calculate_vwap_levels, get_market_session
from trading.signals import generate_trade_recommendation
from trading.risk_management import calculate_position_size
from paper_trading import PaperTrader
from notifications import send_trade_alert, send_market_update, send_daily_summary, send_error_alert

class AutoTrader:
    """Automated trading system"""
    
    def __init__(self):
        self.running = False
        self.trader = PaperTrader()
        self.last_scan_time = None
        self.open_positions = {}
        self.daily_trades = []
        
        # Market hours in HKT
        self.market_open = dt_time(21, 30)  # 9:30 PM HKT
        self.market_close = dt_time(4, 0)    # 4:00 AM HKT next day
    
    def is_market_open(self) -> bool:
        """Check if US market is open"""
        session = get_market_session()
        return session == "REGULAR_MARKET"
    
    def scan_for_signals(self) -> List[Dict]:
        """Scan watchlist for trading signals"""
        signals = []
        
        for symbol in config.DEFAULT_WATCHLIST[:20]:
            try:
                stock_data = fetch_stock_data(symbol)
                quote = stock_data.get('quote')
                df = stock_data.get('history_daily')
                
                if not quote or not quote.get('current_price') or df is None:
                    continue
                
                # Technical analysis
                analyzer = TechnicalAnalyzer(df)
                indicators = analyzer.calculate_all()
                
                # Generate recommendation
                rec = generate_trade_recommendation(quote, indicators)
                
                if rec:
                    rec['current_price'] = quote.get('current_price')
                    signals.append(rec)
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
                continue
        
        # Sort by confidence
        signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return signals
    
    def execute_trade(self, signal: Dict) -> Dict:
        """Execute a paper trade"""
        symbol = signal.get('symbol')
        action = signal.get('action')
        price = signal.get('current_price')
        stop = signal.get('stop_loss', price * 0.98)
        target = signal.get('take_profit', price * 1.05)
        
        if action not in ['BUY', 'SELL']:
            return {'success': False, 'error': 'Invalid action'}
        
        # Calculate position size
        risk_amount = config.CAPITAL * (config.MAX_RISK_PER_TRADE / 100)
        risk_per_share = abs(price - stop)
        
        if risk_per_share > 0:
            shares = int(risk_amount / risk_per_share)
        else:
            shares = 1
        
        shares = min(shares, 100)  # Max 100 shares
        
        if action == 'BUY':
            result = self.trader.buy(symbol, shares, price)
        else:
            result = self.trader.sell(symbol, shares, price)
        
        if result.get('success'):
            # Track position
            self.open_positions[symbol] = {
                'action': action,
                'entry_price': price,
                'stop_loss': stop,
                'take_profit': target,
                'quantity': shares,
                'entry_time': datetime.now().isoformat()
            }
            
            # Send notification
            send_trade_alert(
                symbol=symbol,
                action=action,
                price=price,
                target=target,
                stop=stop,
                confidence=signal.get('confidence', 0.7)
            )
            
            self.daily_trades.append({
                'symbol': symbol,
                'action': action,
                'price': price,
                'quantity': shares,
                'timestamp': datetime.now().isoformat()
            })
        
        return result
    
    def check_positions(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Check open positions for exit signals"""
        closed = []
        
        for symbol, pos in list(self.open_positions.items()):
            current_price = current_prices.get(symbol)
            
            if not current_price:
                continue
            
            action = pos['action']
            entry = pos['entry_price']
            stop = pos['stop_loss']
            target = pos['take_profit']
            
            # Check stop loss
            if action == 'BUY' and current_price <= stop:
                result = self.trader.sell(symbol, pos['quantity'], current_price)
                if result.get('success'):
                    closed.append({'symbol': symbol, 'reason': 'STOP_LOSS', 'price': current_price})
                    del self.open_positions[symbol]
            
            # Check take profit
            elif action == 'BUY' and current_price >= target:
                result = self.trader.sell(symbol, pos['quantity'], current_price)
                if result.get('success'):
                    closed.append({'symbol': symbol, 'reason': 'TAKE_PROFIT', 'price': current_price})
                    del self.open_positions[symbol]
            
            # Check trailing stop (1% below high)
            elif action == 'BUY' and current_price < entry * 0.99:
                result = self.trader.sell(symbol, pos['quantity'], current_price)
                if result.get('success'):
                    closed.append({'symbol': symbol, 'reason': 'TRAILING_STOP', 'price': current_price})
                    del self.open_positions[symbol]
        
        return closed
    
    def run_market_scan(self):
        """Run a complete market scan"""
        print(f"\n{'='*60}")
        print(f"MARKET SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        signals = self.scan_for_signals()
        
        buy_signals = [s for s in signals if s.get('action') == 'BUY']
        sell_signals = [s for s in signals if s.get('action') == 'SELL']
        
        print(f"BUY Signals: {len(buy_signals)}")
        print(f"SELL Signals: {len(sell_signals)}")
        
        # Send notification
        send_market_update(signals)
        
        # Execute top signals if paper trading enabled
        if config.PAPER_TRADING_ENABLED and self.is_market_open():
            for signal in buy_signals[:3]:
                if len(self.open_positions) < config.MAX_CONCURRENT_TRADES:
                    result = self.execute_trade(signal)
                    if result.get('success'):
                        print(f"Executed BUY: {signal['symbol']}")
        
        self.last_scan_time = datetime.now()
        return signals
    
    def run_continuous(self):
        """Run continuous monitoring"""
        print("\n" + "="*60)
        print("AUTOMATED TRADING SYSTEM STARTED")
        print("="*60)
        print(f"Mode: {'PAPER TRADING' if config.PAPER_TRADING_ENABLED else 'LIVE'}")
        print(f"Market Session: {get_market_session()}")
        print(f"Scan Interval: {config.SCAN_INTERVAL_MINUTES} minutes")
        print("="*60)
        
        self.running = True
        
        while self.running:
            try:
                session = get_market_session()
                
                if session == "CLOSED":
                    print(f"[{datetime.now().strftime('%H:%M')}] Market closed. Sleeping 30 min...")
                    time.sleep(1800)  # 30 minutes
                    continue
                
                if session == "PRE_MARKET":
                    print(f"[{datetime.now().strftime('%H:%M')}] Pre-market. Running pre-scan...")
                    self.run_market_scan()
                    time.sleep(1800)  # Sleep until market opens
                    continue
                
                if session == "REGULAR_MARKET":
                    print(f"[{datetime.now().strftime('%H:%M')}] Market open. Scanning...")
                    
                    # Get current prices for position monitoring
                    current_prices = {}
                    for symbol in self.open_positions.keys():
                        try:
                            data = fetch_stock_data(symbol)
                            current_prices[symbol] = data.get('quote', {}).get('current_price', 0)
                        except:
                            pass
                    
                    # Check positions
                    closed = self.check_positions(current_prices)
                    for c in closed:
                        print(f"Closed {c['symbol']}: {c['reason']}")
                    
                    # Scan for new signals
                    self.run_market_scan()
                    
                    # Wait before next scan
                    time.sleep(config.SCAN_INTERVAL_MINUTES * 60)
                    continue
                
                if session == "AFTER_HOURS":
                    print(f"[{datetime.now().strftime('%H:%M')}] After hours. End of day processing...")
                    
                    # Close all positions at market close
                    if self.open_positions:
                        print("Closing all positions for end of day...")
                        for symbol, pos in list(self.open_positions.items()):
                            try:
                                data = fetch_stock_data(symbol)
                                price = data.get('quote', {}).get('current_price', pos['entry_price'])
                                self.trader.sell(symbol, pos['quantity'], price)
                            except:
                                pass
                        self.open_positions.clear()
                    
                    # Send daily summary
                    performance = self.trader.get_performance()
                    send_daily_summary(self.daily_trades, performance.get('pnl', 0))
                    
                    # Reset for next day
                    self.daily_trades = []
                    print("Daily summary sent. System will resume at next market open.")
                    
                    time.sleep(3600)  # Sleep 1 hour
                    continue
                    
            except KeyboardInterrupt:
                print("\nStopping automated trading...")
                self.stop()
                break
            except Exception as e:
                print(f"Error in trading loop: {e}")
                send_error_alert(str(e))
                time.sleep(60)
    
    def stop(self):
        """Stop the trading system"""
        self.running = False
        print("Automated trading stopped.")
    
    def get_status(self) -> Dict:
        """Get current system status"""
        performance = self.trader.get_performance()
        return {
            'running': self.running,
            'market_session': get_market_session(),
            'open_positions': len(self.open_positions),
            'daily_trades': len(self.daily_trades),
            'performance': performance
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Trading System')
    parser.add_argument('--scan', action='store_true', help='Run single market scan')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    trader = AutoTrader()
    
    if args.scan:
        trader.run_market_scan()
    elif args.continuous:
        trader.run_continuous()
    elif args.status:
        status = trader.get_status()
        print(json.dumps(status, indent=2))
    else:
        print("Usage:")
        print("  python auto_trader.py --scan         # Run single scan")
        print("  python auto_trader.py --continuous  # Run continuous monitoring")
        print("  python auto_trader.py --status      # Show system status")


if __name__ == "__main__":
    main()
