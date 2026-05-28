"""
Intraday Trading System - Main Entry Point
Analyzes US market stocks and generates buy/sell recommendations
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from data.fetcher import StockDataFetcher, fetch_stock_data
from analysis.technical import TechnicalAnalyzer, analyze_stock
from scanner.filters import StockScanner
from trading.signals import TradeSignalGenerator, generate_trade_recommendation
from reports.generator import ReportGenerator, generate_recommendations_report

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)


class IntradayTradingSystem:
    """Main trading system class"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.scanner = StockScanner()
        self.signal_generator = TradeSignalGenerator()
        self.report_generator = ReportGenerator()
        self.recommendations = []
        
    def run_analysis(self, symbols: List[str] = None) -> List[Dict]:
        """Run complete analysis on stocks"""
        if symbols is None:
            symbols = config.DEFAULT_WATCHLIST
        
        logger.info(f"Starting analysis on {len(symbols)} stocks...")
        recommendations = []
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"[{i+1}/{len(symbols)}] Analyzing {symbol}...")
                
                # Fetch stock data
                stock_data = fetch_stock_data(symbol)
                quote = stock_data.get('quote')
                history_5min = stock_data.get('history_5min')
                history_daily = stock_data.get('history_daily')
                
                if not quote or not quote.get('current_price'):
                    logger.warning(f"No data for {symbol}, skipping...")
                    continue
                
                # Apply filters
                if not self.scanner.filter_stock(quote):
                    logger.info(f"{symbol} did not pass filters, skipping...")
                    continue
                
                # Calculate technical indicators
                indicators = {}
                if history_5min is not None and not history_5min.empty:
                    analyzer = TechnicalAnalyzer(history_5min)
                    indicators = analyzer.calculate_all()
                elif history_daily is not None and not history_daily.empty:
                    analyzer = TechnicalAnalyzer(history_daily)
                    indicators = analyzer.calculate_all()
                
                # Generate trade recommendation
                recommendation = generate_trade_recommendation(quote, indicators)
                
                if recommendation:
                    recommendation['current_price'] = quote.get('current_price')
                    recommendation['daily_change'] = self._calculate_change(quote)
                    recommendation['volume_ratio'] = self._calculate_volume_ratio(quote)
                    recommendations.append(recommendation)
                    logger.info(f"  -> {symbol}: {recommendation.get('action')} signal generated!")
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Sort recommendations
        recommendations.sort(key=lambda x: (
            0 if x.get('action') == 'BUY' else 1,
            -x.get('composite_score', 0) if x.get('action') == 'BUY' else x.get('composite_score', 0)
        ))
        
        self.recommendations = recommendations
        return recommendations
    
    def _calculate_change(self, quote: Dict) -> float:
        """Calculate daily price change percentage"""
        current = quote.get('current_price', 0)
        previous = quote.get('previous_close', 0)
        if current and previous and previous > 0:
            return ((current - previous) / previous) * 100
        return 0.0
    
    def _calculate_volume_ratio(self, quote: Dict) -> float:
        """Calculate volume ratio"""
        volume = quote.get('volume', 0)
        avg_volume = quote.get('avg_volume', 0)
        if volume and avg_volume and avg_volume > 0:
            return volume / avg_volume
        return 0.0
    
    def generate_reports(self) -> Dict:
        """Generate analysis reports"""
        return generate_recommendations_report(self.recommendations)
    
    def print_summary(self):
        """Print analysis summary to console"""
        print("\n" + "="*80)
        print("INTRADAY TRADING ANALYSIS SUMMARY")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} HKT")
        print(f"Capital: ${config.CAPITAL:,} | Max Risk/Trade: ${config.MAX_RISK_PER_TRADE}")
        print("-"*80)
        
        buy_recs = [r for r in self.recommendations if r.get('action') == 'BUY']
        sell_recs = [r for r in self.recommendations if r.get('action') == 'SELL']
        
        print(f"\n[BUY] BUY SIGNALS: {len(buy_recs)}")
        print("-"*40)
        
        for rec in buy_recs[:10]:  # Top 10
            symbol = rec.get('symbol', 'N/A')
            entry = rec.get('entry_price', 0)
            target = rec.get('take_profit', 0)
            stop = rec.get('stop_loss', 0)
            rr = rec.get('risk_reward_ratio', 0)
            conf = rec.get('confidence', 'LOW')
            shares = rec.get('shares', 0)
            cost = rec.get('total_cost', 0)
            
            print(f"  {symbol:8} | Entry: ${entry:.2f} | Target: ${target:.2f} | Stop: ${stop:.2f} | R/R: {rr:.1f}x | {conf}")
            print(f"             Shares: {shares} | Cost: ${cost:.2f}")
        
        if sell_recs:
            print(f"\n[SELL] SELL SIGNALS: {len(sell_recs)}")
            print("-"*40)
            for rec in sell_recs[:5]:
                symbol = rec.get('symbol', 'N/A')
                entry = rec.get('entry_price', 0)
                target = rec.get('take_profit', 0)
                stop = rec.get('stop_loss', 0)
                rr = rec.get('risk_reward_ratio', 0)
                conf = rec.get('confidence', 'LOW')
                print(f"  {symbol:8} | Entry: ${entry:.2f} | Target: ${target:.2f} | Stop: ${stop:.2f} | R/R: {rr:.1f}x | {conf}")
        
        print("\n" + "="*80)
        print("[WARNING] DISCLAIMER: This is not financial advice. Trade at your own risk.")
        print("="*80 + "\n")


def main():
    """Main entry point"""
    print("\n[START] Intraday Trading Analysis System...")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} HKT")
    print(f"[CAPITAL] ${config.CAPITAL:,}")
    print("-"*60)
    
    # Initialize system
    system = IntradayTradingSystem()
    
    # Run analysis
    recommendations = system.run_analysis()
    
    # Print summary
    system.print_summary()
    
    # Generate reports (always, even if empty)
    reports = system.generate_reports()
    print(f"\n[REPORTS] Reports generated:")
    print(f"   JSON: {reports.get('json', 'N/A')}")
    print(f"   HTML: {reports.get('html', 'N/A')}")
    
    if recommendations:
        print(f"\n   Open the HTML file in your browser to view recommendations!")
    else:
        print("\n[WARNING] No trade recommendations generated.")
        print("   This could mean:")
        print("   - No stocks passed the filters")
        print("   - No strong buy/sell signals detected")
        print("   - Market conditions not favorable")
    
    return recommendations


if __name__ == "__main__":
    main()