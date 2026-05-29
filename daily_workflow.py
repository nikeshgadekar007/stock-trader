"""
Daily Trading Workflow Script
Run this every day before trading
"""

import sys
from datetime import datetime
from data.fetcher import fetch_stock_data
from analysis.technical import TechnicalAnalyzer, analyze_stock
from analysis.sentiment import analyze_news
from analysis.intraday import get_intraday_signal, calculate_vwap_levels, get_market_session
from trading.risk_management import get_risk_assessment, TradeSetup
from scanner.watchlist import Watchlist, get_default_watchlist

def get_signal_from_indicators(indicators: dict) -> dict:
    """Generate signal from technical indicators"""
    rsi = indicators.get('rsi', {}).get('rsi', 50)
    macd_trend = indicators.get('macd', {}).get('trend', 'neutral')
    stoch_signal = indicators.get('stochastic', {}).get('signal', 'neutral')
    
    buy_signals = 0
    sell_signals = 0
    
    if rsi < 30:
        buy_signals += 1
    elif rsi > 70:
        sell_signals += 1
    
    if macd_trend == 'bullish':
        buy_signals += 1
    elif macd_trend == 'bearish':
        sell_signals += 1
    
    if stoch_signal == 'oversold':
        buy_signals += 1
    elif stoch_signal == 'overbought':
        sell_signals += 1
    
    total = buy_signals + sell_signals
    if total == 0:
        return {'signal': 'HOLD', 'confidence': 0.5, 'rsi': rsi}
    
    if buy_signals > sell_signals:
        confidence = buy_signals / total
        if buy_signals >= 3:
            return {'signal': 'STRONG_BUY', 'confidence': confidence, 'rsi': rsi}
        return {'signal': 'BUY', 'confidence': confidence, 'rsi': rsi}
    elif sell_signals > buy_signals:
        confidence = sell_signals / total
        if sell_signals >= 3:
            return {'signal': 'STRONG_SELL', 'confidence': confidence, 'rsi': rsi}
        return {'signal': 'SELL', 'confidence': confidence, 'rsi': rsi}
    else:
        return {'signal': 'HOLD', 'confidence': 0.5, 'rsi': rsi}

def scan_watchlist():
    """Scan all stocks in watchlist"""
    print("=" * 60)
    print("DAILY STOCK SCANNER")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    wl = Watchlist()
    symbols = get_default_watchlist()
    
    if not wl.get_watchlist():
        for symbol in symbols:
            wl.add(symbol)
    
    results = []
    
    for symbol in symbols[:10]:
        try:
            print(f"Analyzing {symbol}...")
            stock_data = fetch_stock_data(symbol)
            df = stock_data.get('history_daily')
            
            if df is None or len(df) < 50:
                print(f"  Skipping {symbol} - insufficient data")
                continue
            
            indicators = analyze_stock(df)
            signal = get_signal_from_indicators(indicators)
            news = analyze_news(symbol)
            
            if signal['signal'] in ['BUY', 'STRONG_BUY'] and news['overall_sentiment'] == 'POSITIVE':
                final_signal = 'STRONG_BUY'
            elif signal['signal'] in ['SELL', 'STRONG_SELL'] and news['overall_sentiment'] == 'NEGATIVE':
                final_signal = 'STRONG_SELL'
            else:
                final_signal = signal['signal']
            
            results.append({
                'symbol': symbol,
                'signal': final_signal,
                'confidence': signal['confidence'],
                'news_sentiment': news['overall_sentiment'],
                'price': df['close'].iloc[-1] if 'close' in df.columns else 0
            })
            
            print(f"  Signal: {final_signal} ({signal['confidence']:.0%})")
            print(f"  News: {news['overall_sentiment']}")
            print()
            
        except Exception as e:
            print(f"  Error analyzing {symbol}: {e}")
            continue
    
    buy_signals = [r for r in results if r['signal'] in ['BUY', 'STRONG_BUY']]
    sell_signals = [r for r in results if r['signal'] in ['SELL', 'STRONG_SELL']]
    
    print("=" * 60)
    print("TOP BUY SIGNALS")
    print("=" * 60)
    for r in sorted(buy_signals, key=lambda x: x['confidence'], reverse=True)[:5]:
        print(f"  {r['symbol']}: {r['signal']} ({r['confidence']:.0%}) - ${r['price']:.2f}")
    
    print()
    print("=" * 60)
    print("TOP SELL SIGNALS")
    print("=" * 60)
    for r in sorted(sell_signals, key=lambda x: x['confidence'], reverse=True)[:5]:
        print(f"  {r['symbol']}: {r['signal']} ({r['confidence']:.0%}) - ${r['price']:.2f}")
    
    print()
    print("=" * 60)
    print("READY TO TRADE")
    print("=" * 60)
    
    if buy_signals:
        top_buy = sorted(buy_signals, key=lambda x: x['confidence'], reverse=True)[0]
        print(f"\nTOP PICK: {top_buy['symbol']}")
        print(f"  Signal: {top_buy['signal']}")
        print(f"  Confidence: {top_buy['confidence']:.0%}")
        print(f"  News Sentiment: {top_buy['news_sentiment']}")
        print(f"  Current Price: ${top_buy['price']:.2f}")
    
    return results

def analyze_single_stock(symbol: str):
    """Analyze a single stock"""
    print("=" * 60)
    print(f"STOCK ANALYSIS: {symbol}")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    stock_data = fetch_stock_data(symbol)
    df = stock_data.get('history_daily')
    
    if df is None or len(df) < 50:
        print(f"Error: Insufficient data for {symbol}")
        return
    
    current_price = df['close'].iloc[-1]
    print(f"Current Price: ${current_price:.2f}")
    print()
    
    indicators = analyze_stock(df)
    signal = get_signal_from_indicators(indicators)
    
    print("TECHNICAL INDICATORS:")
    if signal.get('rsi'):
        print(f"  RSI: {signal['rsi']:.1f}")
    print(f"  Signal: {signal['signal']}")
    print(f"  Confidence: {signal['confidence']:.0%}")
    print()
    
    if signal['signal'] in ['BUY', 'STRONG_BUY']:
        print("TRADE SETUP (BUY):")
        print(f"  Entry: ${current_price:.2f}")
        print(f"  Stop Loss: ${current_price * 0.98:.2f} (-2%)")
        print(f"  Target: ${current_price * 1.05:.2f} (+5%)")
    elif signal['signal'] in ['SELL', 'STRONG_SELL']:
        print("TRADE SETUP (SELL):")
        print(f"  Entry: ${current_price:.2f}")
        print(f"  Stop Loss: ${current_price * 1.02:.2f} (+2%)")
        print(f"  Target: ${current_price * 0.95:.2f} (-5%)")
    else:
        print("No trade setup - HOLD signal")
    
    print()
    news = analyze_news(symbol)
    print("NEWS SENTIMENT:")
    print(f"  Overall: {news['overall_sentiment']}")
    print(f"  Articles: {news['article_count']}")
    print(f"  Positive: {news['positive_count']}, Negative: {news['negative_count']}")

def analyze_intraday(symbol: str):
    """Intraday analysis for day trading"""
    print("=" * 60)
    print(f"INTRADAY ANALYSIS: {symbol}")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Market Session: {get_market_session()}")
    print()
    
    stock_data = fetch_stock_data(symbol)
    df = stock_data.get('history_daily')
    
    if df is None or len(df) < 50:
        print(f"Error: Insufficient data for {symbol}")
        return
    
    current_price = df['close'].iloc[-1]
    print(f"Current Price: ${current_price:.2f}")
    print()
    
    # VWAP Analysis
    vwap_data = calculate_vwap_levels(df)
    if vwap_data:
        print("VWAP ANALYSIS:")
        print(f"  VWAP: ${vwap_data['vwap']:.2f}")
        print(f"  Position: {vwap_data['position'].upper()} VWAP")
        print(f"  Distance: {vwap_data['distance_percent']:.2f}%")
        print(f"  Upper Band: ${vwap_data['upper_band']:.2f}")
        print(f"  Lower Band: ${vwap_data['lower_band']:.2f}")
        print()
    
    # Intraday Signal
    intraday = get_intraday_signal(df)
    print("INTRADAY SIGNALS:")
    for sig in intraday.get('details', {}).get('signals', []):
        print(f"  - {sig}")
    print()
    print(f"Final Signal: {intraday['signal']} ({intraday['confidence']:.0%})")
    print()
    
    # Entry/Exit for intraday
    if vwap_data:
        print("INTRADAY TRADE SETUP:")
        if intraday['signal'] == 'BUY':
            print(f"  Entry: ${current_price:.2f}")
            print(f"  VWAP Support: ${vwap_data['vwap']:.2f}")
            print(f"  Stop Loss: ${vwap_data['lower_band']:.2f}")
            print(f"  Target: ${vwap_data['upper_band']:.2f}")
        else:
            print(f"  Entry: ${current_price:.2f}")
            print(f"  VWAP Resistance: ${vwap_data['vwap']:.2f}")
            print(f"  Stop Loss: ${vwap_data['upper_band']:.2f}")
            print(f"  Target: ${vwap_data['lower_band']:.2f}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--scan':
            scan_watchlist()
        elif sys.argv[1] == '--intraday' and len(sys.argv) > 2:
            analyze_intraday(sys.argv[2].upper())
        else:
            analyze_single_stock(sys.argv[1].upper())
    else:
        print("Usage:")
        print("  python daily_workflow.py --scan        # Scan watchlist")
        print("  python daily_workflow.py --intraday AAPL  # Intraday analysis")
        print("  python daily_workflow.py AAPL         # Single stock analysis")
