"""
NLP News Trading Module
Real-time news sentiment analysis for stock trading
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# Sentiment analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from textblob import TextBlob
    ANALYZER = SentimentIntensityAnalyzer()
except ImportError:
    ANALYZER = None

class NLPNewsAnalyzer:
    """NLP-powered news analysis for trading signals"""
    
    def __init__(self):
        self.analyzer = ANALYZER
        self.newsapi_key = os.environ.get('NEWSAPI_KEY')  # Optional
        
    def analyze_stock_news(self, symbol: str) -> Dict:
        """Analyze news for a specific stock"""
        news = self.fetch_news(symbol)
        sentiment = self.analyze_sentiment(news)
        impact = self.calculate_impact(sentiment)
        
        return {
            'symbol': symbol,
            'news': news,
            'sentiment': sentiment,
            'impact_score': impact,
            'recommendation': self.generate_recommendation(sentiment, impact),
            'timestamp': datetime.now().isoformat()
        }
    
    def fetch_news(self, symbol: str) -> List[Dict]:
        """Fetch recent news for a stock"""
        news_list = []
        
        # Try Yahoo Finance news (free, no API key)
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount=10"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('news', [])
                
                for article in articles:
                    news_list.append({
                        'title': article.get('title', ''),
                        'description': article.get('summary', article.get('description', '')),
                        'source': article.get('publisher', 'Unknown'),
                        'url': article.get('link', ''),
                        'published': article.get('pubDate', ''),
                        'type': article.get('type', 'news')
                    })
        except Exception as e:
            print(f"Yahoo Finance news error: {e}")
        
        # Try alternative: FMP (Free tier available)
        try:
            fmp_url = f"https://financialmodelingprep.com/api/v3/fmp/articles?page=0&size=10&apikey=demo"
            response = requests.get(fmp_url, timeout=10)
            if response.status_code == 200:
                articles = response.json()
                for article in articles[:5]:
                    news_list.append({
                        'title': article.get('title', ''),
                        'description': article.get('text', ''),
                        'source': article.get('source', 'FMP'),
                        'url': article.get('url', ''),
                        'published': article.get('publishedDate', ''),
                        'type': 'article'
                    })
        except:
            pass
        
        return news_list[:10]  # Return top 10
    
    def analyze_sentiment(self, news: List[Dict]) -> Dict:
        """Analyze sentiment of news articles"""
        if not news or not self.analyzer:
            return {
                'overall': 'NEUTRAL',
                'score': 0.0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'avg_compound': 0.0
            }
        
        scores = []
        positive = 0
        negative = 0
        neutral = 0
        
        for article in news:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            
            if text.strip():
                # VADER sentiment
                vader_scores = self.analyzer.polarity_scores(text)
                compound = vader_scores['compound']
                scores.append(compound)
                
                if compound >= 0.05:
                    positive += 1
                elif compound <= -0.05:
                    negative += 1
                else:
                    neutral += 1
        
        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0.0
        
        # Determine overall sentiment
        if avg_score >= 0.1:
            overall = 'POSITIVE'
        elif avg_score <= -0.1:
            overall = 'NEGATIVE'
        else:
            overall = 'NEUTRAL'
        
        return {
            'overall': overall,
            'score': avg_score,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'avg_compound': avg_score,
            'total_articles': len(news)
        }
    
    def calculate_impact(self, sentiment: Dict) -> Dict:
        """Calculate potential price impact"""
        score = abs(sentiment.get('avg_compound', 0))
        total = sentiment.get('total_articles', 0)
        
        # Impact based on sentiment strength and article count
        if score >= 0.5 and total >= 5:
            impact = 'HIGH'
        elif score >= 0.3 and total >= 3:
            impact = 'MEDIUM'
        elif score >= 0.1 and total >= 1:
            impact = 'LOW'
        else:
            impact = 'MINIMAL'
        
        return {
            'level': impact,
            'strength': score,
            'momentum': 'BULLISH' if sentiment.get('avg_compound', 0) > 0 else 'BEARISH'
        }
    
    def generate_recommendation(self, sentiment: Dict, impact: Dict) -> Dict:
        """Generate trading recommendation based on sentiment"""
        sentiment_score = sentiment.get('avg_compound', 0)
        impact_level = impact.get('level', 'MINIMAL')
        
        if impact_level == 'HIGH' and sentiment_score > 0.3:
            action = 'STRONG_BUY'
            confidence = 0.85
        elif impact_level == 'HIGH' and sentiment_score < -0.3:
            action = 'STRONG_SELL'
            confidence = 0.85
        elif impact_level == 'MEDIUM' and sentiment_score > 0.1:
            action = 'BUY'
            confidence = 0.70
        elif impact_level == 'MEDIUM' and sentiment_score < -0.1:
            action = 'SELL'
            confidence = 0.70
        elif impact_level == 'LOW':
            action = 'HOLD'
            confidence = 0.50
        else:
            action = 'NEUTRAL'
            confidence = 0.40
        
        return {
            'action': action,
            'confidence': confidence,
            'reasoning': f"Impact: {impact_level}, Sentiment: {sentiment.get('overall', 'NEUTRAL')}"
        }
    
    def scan_watchlist_sentiment(self, symbols: List[str]) -> List[Dict]:
        """Scan multiple stocks for sentiment"""
        results = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_stock_news(symbol)
                results.append(analysis)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
        
        # Sort by impact score
        results.sort(key=lambda x: abs(x['sentiment']['avg_compound']), reverse=True)
        
        return results
    
    def get_earnings_impact(self, symbol: str) -> Dict:
        """Check for upcoming earnings and estimate impact"""
        # This would integrate with earnings calendar API
        # For now, return placeholder
        return {
            'has_earnings': False,
            'days_until': None,
            'expected_move': None,
            'historical_volatility': None
        }


def analyze_news(symbol: str) -> Dict:
    """Quick function to analyze news for a symbol"""
    analyzer = NLPNewsAnalyzer()
    return analyzer.analyze_stock_news(symbol)


def scan_sentiment(symbols: List[str]) -> List[Dict]:
    """Scan multiple symbols for sentiment"""
    analyzer = NLPNewsAnalyzer()
    return analyzer.scan_watchlist_sentiment(symbols)