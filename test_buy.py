"""Test BUY signal generation"""
import sys
sys.path.insert(0, '.')

from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer
from trading.signals import generate_trade_recommendation

# Test with AAPL
print("Testing AAPL...")
data = fetch_stock_data('AAPL')
quote = data.get('quote')
df = data.get('history_daily')

print(f"Quote: {quote}")
print(f"DF shape: {df.shape if df is not None else 'None'}")

analyzer = TechnicalAnalyzer(df)
indicators = analyzer.calculate_all()

print(f"Indicators: {indicators}")

rec = generate_trade_recommendation(quote, indicators)
print(f"Recommendation: {rec}")