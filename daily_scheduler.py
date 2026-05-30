"""
Daily Trading Scheduler
Automates the complete trading workflow throughout the day
"""

import schedule
import time
import threading
from datetime import datetime
from typing import Callable, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notifications import NotificationService
from reports.generator import DailyReportGenerator
from trading.portfolio import Portfolio
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer
from analysis.nlp_news import NLPNewsAnalyzer
from trading.signals import generate_trade_recommendation
import config

class DailyScheduler:
    """Schedules and executes daily trading tasks"""
    
    def __init__(self):
        self.notifier = NotificationService()
        self.reporter = DailyReportGenerator()
        self.portfolio = Portfolio()
        self.running = False
        self.thread = None
        
    def premarket_setup(self):
        """Start of day: Fetch data, analyze, prepare signals"""
        print(f"[{datetime.now()}] PRE-MARKET: Starting daily setup...")
        
        try:
            # Fetch data for all watchlist stocks
            signals = []
            for symbol in config.DEFAULT_WATCHLIST[:20]:
                try:
                    stock_data = fetch_stock_data(symbol)
                    df = stock_data.get('history_daily')
                    quote = stock_data.get('quote')
                    
                    if df is not None and quote:
                        analyzer = TechnicalAnalyzer(df)
                        indicators = analyzer.calculate_all()
                        rec = generate_trade_recommendation(quote, indicators)
                        if rec:
                            signals.append(rec)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
            
            # Filter strong signals
            strong_signals = [s for s in signals if s.get('confidence', 0) >= 0.7]
            
            # Send morning notification
            message = f"📊 **Morning Scan Complete**\n\n"
            message += f"Found {len(strong_signals)} strong signals\n\n"
            
            if strong_signals:
                buy_signals = [s for s in strong_signals if 'BUY' in s.get('action', '')]
                sell_signals = [s for s in strong_signals if 'SELL' in s.get('action', '')]
                
                if buy_signals:
                    message += "🟢 **BUY Signals:**\n"
                    for s in buy_signals[:3]:
                        message += f"- {s['symbol']} @ ${s.get('current_price', 0):.2f}\n"
                    message += "\n"
                
                if sell_signals:
                    message += "🔴 **SELL Signals:**\n"
                    for s in sell_signals[:3]:
                        message += f"- {s['symbol']} @ ${s.get('current_price', 0):.2f}\n"
            
            self.notifier.send_trade_alert(message)
            print(f"[{datetime.now()}] PRE-MARKET: Setup complete, {len(strong_signals)} signals found")
            
        except Exception as e:
            print(f"Pre-market error: {e}")
    
    def intraday_scan(self):
        """During market: Scan for signals"""
        print(f"[{datetime.now()}] INTRADAY: Scanning for signals...")
        
        try:
            # Quick scan
            analyzer = NLPNewsAnalyzer()
            symbols = config.DEFAULT_WATCHLIST[:10]
            results = analyzer.scan_watchlist_sentiment(symbols)
            
            # Find high-impact signals
            high_impact = [r for r in results if r['impact_score']['level'] == 'HIGH']
            
            if high_impact:
                message = f"🚨 **High Impact Alert**\n\n"
                for r in high_impact[:3]:
                    sentiment = r['sentiment']
                    message += f"{r['symbol']}: {sentiment['overall']} (Score: {sentiment['avg_compound']:.2f})\n"
                
                self.notifier.send_trade_alert(message)
                print(f"[{datetime.now()}] INTRADAY: {len(high_impact)} high-impact signals found")
            
        except Exception as e:
            print(f"Intraday scan error: {e}")
    
    def market_close(self):
        """End of day: Log trades, generate report, retrain"""
        print(f"[{datetime.now()}] MARKET CLOSE: Starting end-of-day tasks...")
        
        try:
            # Generate daily report
            report = self.reporter.generate_daily_report()
            
            # Send report
            self.notifier.send_daily_report(report)
            
            # Trigger model retraining (async)
            self.trigger_retraining()
            
            print(f"[{datetime.now()}] MARKET CLOSE: End-of-day tasks complete")
            
        except Exception as e:
            print(f"Market close error: {e}")
    
    def trigger_retraining(self):
        """Trigger model retraining in background"""
        print(f"[{datetime.now()}] RETRAIN: Starting model retraining...")
        
        try:
            # Import and run retraining
            from train_model import retrain_model
            
            # Run retraining with recent data
            success = retrain_model()
            
            if success:
                self.notifier.send_trade_alert("✅ Model retrained successfully with today's data")
            else:
                self.notifier.send_trade_alert("⚠️ Model retraining failed, using previous model")
                
        except Exception as e:
            print(f"Retraining error: {e}")
    
    def schedule_tasks(self):
        """Schedule all daily tasks"""
        # Pre-market: 9:00 AM ET (14:00 UTC)
        schedule.every().day.at("14:00").do(self.premarket_setup)
        
        # Intraday scans: Every 30 minutes during market hours
        schedule.every().day.at("14:30").do(self.intraday_scan)
        schedule.every().day.at("15:00").do(self.intraday_scan)
        schedule.every().day.at("15:30").do(self.intraday_scan)
        schedule.every().day.at("16:00").do(self.intraday_scan)
        schedule.every().day.at("16:30").do(self.intraday_scan)
        schedule.every().day.at("17:00").do(self.intraday_scan)
        schedule.every().day.at("17:30").do(self.intraday_scan)
        schedule.every().day.at("18:00").do(self.intraday_scan)
        schedule.every().day.at("18:30").do(self.intraday_scan)
        schedule.every().day.at("19:00").do(self.intraday_scan)
        schedule.every().day.at("19:30").do(self.intraday_scan)
        schedule.every().day.at("20:00").do(self.intraday_scan)
        
        # Market close: 4:00 PM ET (21:00 UTC)
        schedule.every().day.at("21:00").do(self.market_close)
        
        print("Tasks scheduled:")
        print("  - Pre-market: 9:00 AM ET")
        print("  - Intraday scans: Every 30 min (9:30 AM - 4:00 PM ET)")
        print("  - Market close: 4:00 PM ET")
    
    def run_continuously(self):
        """Run scheduler in background thread"""
        self.running = True
        self.schedule_tasks()
        
        def run():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        print("Scheduler started in background")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Scheduler stopped")


def run_scheduler():
    """Run the scheduler"""
    scheduler = DailyScheduler()
    scheduler.run_continuously()
    
    print("\n" + "="*50)
    print("DAILY TRADING SCHEDULER")
    print("="*50)
    print("\nScheduler running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()


if __name__ == "__main__":
    run_scheduler()