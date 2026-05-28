"""Test technical analysis and signals"""
import yfinance as yf
from analysis.technical import TechnicalAnalyzer
from trading.signals import generate_trade_recommendation

print("=== Testing Technical Analysis ===")

# Get AAPL data
ticker = yf.Ticker('AAPL')
info = ticker.info

# Get historical data
df = ticker.history(period='1mo')
print(f"Historical data rows: {len(df)}")

if not df.empty:
    df = df.reset_index()
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    print(f"Columns: {list(df.columns)}")
    
    # Calculate indicators
    analyzer = TechnicalAnalyzer(df)
    indicators = analyzer.calculate_all()
    
    print(f"\nIndicators:")
    print(f"RSI: {indicators.get('rsi', {})}")
    print(f"MACD: {indicators.get('macd', {})}")
    print(f"Stochastic: {indicators.get('stochastic', {})}")
    print(f"Signals: {indicators.get('signals', {})}")
    
    # Create quote
    quote = {
        'symbol': 'AAPL',
        'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
        'previous_close': info.get('previousClose') or info.get('regularMarketPreviousClose'),
        'volume': info.get('volume'),
        'avg_volume': info.get('averageVolume')
    }
    
    print(f"\nQuote: {quote}")
    
    # Generate recommendation
    rec = generate_trade_recommendation(quote, indicators)
    print(f"\nRecommendation: {rec}")