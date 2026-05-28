"""
News Sentiment Analysis for Stock Trading
Uses basic NLP to analyze news headlines
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Simple sentiment lexicon (no external dependencies)
POSITIVE_WORDS = {
    'beat', 'beats', 'bullish', 'buy', 'buying', 'gain', 'gains', 'growth',
    'higher', 'increase', 'increased', 'outperform', 'positive', 'profit',
    'profits', 'rally', 'rise', 'rising', 'strong', 'stronger', 'surge',
    'upbeat', 'upgrade', 'upside', 'win', 'winning', 'soar', 'soared',
    'jump', 'jumped', 'record', 'high', 'highs', 'best', 'exceed', 'exceeded'
}

NEGATIVE_WORDS = {
    'bearish', 'break', 'broke', 'crash', 'crashed', 'decline', 'declined',
    'drop', 'dropped', 'fail', 'failed', 'fall', 'fell', 'fear', 'fraud',
    'investigation', 'lawsuit', 'loss', 'losses', 'lower', 'miss', 'missed',
    'negative', 'plunge', 'plunged', 'problem', 'problems', 'prosecutor',
    'recall', 'recall', 'risk', 'sell', 'selling', 'slump', 'slumped',
    'subpoena', 'sue', 'sued', 'suit', 'suspend', 'suspended', 'investigate',
    'downgrade', 'cut', 'cutting', 'layoff', 'layoffs', 'warning', 'warned'
}

def analyze_headline(headline: str) -> Dict:
    """Analyze a single headline for sentiment"""
    words = headline.lower().split()
    
    positive_count = sum(1 for w in words if w in POSITIVE_WORDS)
    negative_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    
    total = positive_count + negative_count
    
    if total == 0:
        sentiment = 'NEUTRAL'
        score = 0
    elif positive_count > negative_count:
        sentiment = 'POSITIVE'
        score = positive_count / total
    elif negative_count > positive_count:
        sentiment = 'NEGATIVE'
        score = -negative_count / total
    else:
        sentiment = 'NEUTRAL'
        score = 0
    
    return {
        'sentiment': sentiment,
        'score': score,
        'positive_count': positive_count,
        'negative_count': negative_count
    }

def fetch_news(symbol: str, days: int = 7) -> List[Dict]:
    """Fetch recent news for a symbol"""
    try:
        import yfinance
        ticker = yfinance.Ticker(symbol)
        news = ticker.news
        
        results = []
        for item in news[:20]:  # Limit to 20 articles
            results.append({
                'title': item.get('title', ''),
                'publisher': item.get('publisher', 'Unknown'),
                'link': item.get('link', ''),
                'published': item.get('pubDate', '')
            })
        
        return results
    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")
        return []

def analyze_news(symbol: str) -> Dict:
    """Get comprehensive news sentiment for a symbol"""
    news = fetch_news(symbol)
    
    if not news:
        return {
            'symbol': symbol,
            'overall_sentiment': 'NO_DATA',
            'sentiment_score': 0,
            'article_count': 0,
            'positive_count': 0,
            'negative_count': 0,
            'news': []
        }
    
    analyses = []
    for article in news:
        analysis = analyze_headline(article['title'])
        article['analysis'] = analysis
        analyses.append(analysis)
    
    positive = sum(1 for a in analyses if a['sentiment'] == 'POSITIVE')
    negative = sum(1 for a in analyses if a['sentiment'] == 'NEGATIVE')
    neutral = sum(1 for a in analyses if a['sentiment'] == 'NEUTRAL')
    
    avg_score = sum(a['score'] for a in analyses) / len(analyses)
    
    if avg_score > 0.1:
        overall = 'POSITIVE'
    elif avg_score < -0.1:
        overall = 'NEGATIVE'
    else:
        overall = 'NEUTRAL'
    
    return {
        'symbol': symbol,
        'overall_sentiment': overall,
        'sentiment_score': avg_score,
        'article_count': len(news),
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'news': news
    }

def get_trading_signal(symbol: str, technical_signal: str, confidence: float) -> Dict:
    """Combine news sentiment with technical analysis for final signal"""
    news_analysis = analyze_news(symbol)
    
    sentiment_boost = news_analysis['sentiment_score'] * 0.2
    
    # Adjust confidence based on sentiment
    adjusted_confidence = confidence + sentiment_boost
    
    # Final signal logic
    if adjusted_confidence > 0.7:
        final_signal = 'STRONG_BUY'
    elif adjusted_confidence > 0.5:
        final_signal = 'BUY'
    elif adjusted_confidence < 0.3:
        final_signal = 'STRONG_SELL'
    elif adjusted_confidence < 0.5:
        final_signal = 'SELL'
    else:
        final_signal = 'HOLD'
    
    return {
        'symbol': symbol,
        'technical_signal': technical_signal,
        'news_sentiment': news_analysis['overall_sentiment'],
        'final_signal': final_signal,
        'confidence': adjusted_confidence,
        'news_analysis': news_analysis
    }

if __name__ == "__main__":
    # Test
    result = analyze_news('AAPL')
    print(f"\nAAPL News Sentiment: {result['overall_sentiment']}")
    print(f"Articles: {result['article_count']}")
    print(f"Positive: {result['positive_count']}, Negative: {result['negative_count']}")