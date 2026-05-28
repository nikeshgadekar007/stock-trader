"""Quick test to debug data flow"""
import yfinance as yf
import config
from scanner.filters import StockScanner

print("=== Testing Data Flow ===")
print(f"MIN_PRICE: {config.MIN_PRICE}")
print(f"MAX_PRICE: {config.MAX_PRICE}")
print(f"MIN_VOLUME: {config.MIN_VOLUME}")
print(f"MIN_PRICE_CHANGE_PCT: {config.MIN_PRICE_CHANGE_PCT}")
print(f"MAX_PRICE_CHANGE_PCT: {config.MAX_PRICE_CHANGE_PCT}")

# Test AAPL
print("\n=== Testing AAPL ===")
ticker = yf.Ticker('AAPL')
info = ticker.info

price = info.get('currentPrice') or info.get('regularMarketPrice')
volume = info.get('volume') or info.get('regularMarketVolume')
prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose')

print(f"Current Price: {price}")
print(f"Volume: {volume}")
print(f"Previous Close: {prev_close}")

if price and prev_close:
    change_pct = ((price - prev_close) / prev_close) * 100
    print(f"Change %: {change_pct:.2f}%")

# Test scanner
print("\n=== Testing Scanner ===")
scanner = StockScanner()
quote = {
    'symbol': 'AAPL',
    'current_price': price,
    'volume': volume,
    'previous_close': prev_close
}

print(f"Quote: {quote}")
print(f"Price filter: {scanner.filter_by_price(quote)}")
print(f"Volume filter: {scanner.filter_by_volume(quote)}")
print(f"Price change filter: {scanner.filter_by_price_change(quote)}")
print(f"Overall filter: {scanner.filter_stock(quote)}")