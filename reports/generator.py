"""
Report Generator
Generates HTML reports and JSON outputs
"""

import json
import os
from datetime import datetime
from typing import Dict, List
import config


class ReportGenerator:
    """Generates analysis reports"""
    
    def __init__(self):
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(config.CHARTS_DIR, exist_ok=True)
        
    def generate_json_report(self, recommendations: List[Dict]) -> str:
        """Generate JSON report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'capital': config.CAPITAL,
            'max_risk_per_trade': config.MAX_RISK_PER_TRADE,
            'recommendations': recommendations,
            'summary': {
                'total_recommendations': len(recommendations),
                'buy_signals': len([r for r in recommendations if r.get('action') == 'BUY']),
                'sell_signals': len([r for r in recommendations if r.get('action') == 'SELL'])
            }
        }
        
        filepath = config.RECOMMENDATIONS_FILE
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return filepath
    
    def generate_html_report(self, recommendations: List[Dict], market_data: Dict = None) -> str:
        """Generate HTML report"""
        buy_count = len([r for r in recommendations if r.get('action') == 'BUY'])
        sell_count = len([r for r in recommendations if r.get('action') == 'SELL'])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>Intraday Trading Recommendations</title>',
            '<style>',
            'body { font-family: Arial, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }',
            '.header { text-align: center; margin-bottom: 30px; }',
            '.header h1 { color: #00d4ff; }',
            '.stats { display: flex; gap: 20px; margin-bottom: 30px; }',
            '.stat-card { background: #1a1a2e; padding: 20px; border-radius: 10px; flex: 1; text-align: center; }',
            '.stat-card .value { font-size: 2em; font-weight: bold; color: #00d4ff; }',
            '.rec-card { background: #1a1a2e; border-radius: 15px; padding: 25px; margin-bottom: 20px; border-left: 5px solid #00d4ff; }',
            '.rec-card.sell { border-left-color: #ff4757; }',
            '.rec-card .symbol { font-size: 2em; font-weight: bold; }',
            '.action { display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; }',
            '.action.buy { background: #00d4ff; color: #000; }',
            '.action.sell { background: #ff4757; color: #fff; }',
            '.confidence { display: inline-block; padding: 5px 15px; border-radius: 20px; margin-left: 10px; }',
            '.confidence.high { background: #00ff88; color: #000; }',
            '.confidence.medium { background: #ffaa00; color: #000; }',
            '.confidence.low { background: #888; color: #fff; }',
            '.prices { display: flex; gap: 15px; margin-top: 20px; }',
            '.price-box { background: #16213e; padding: 15px; border-radius: 10px; flex: 1; text-align: center; }',
            '.price-box .value { font-size: 1.5em; font-weight: bold; }',
            '.entry { color: #00d4ff; }',
            '.target { color: #00ff88; }',
            '.stop { color: #ff4757; }',
            '.reason { margin-top: 15px; padding: 15px; background: #16213e; border-radius: 10px; }',
            '.footer { text-align: center; margin-top: 40px; color: #666; }',
            '</style>',
            '</head>',
            '<body>',
            '<div class="header">',
            '<h1>Intraday Trading Recommendations</h1>',
            '<p>Generated: ' + timestamp + ' HKT | US Market Analysis</p>',
            '</div>',
            '<div class="stats">',
            '<div class="stat-card">',
            '<div class="value">' + str(len(recommendations)) + '</div>',
            '<div>Total Recommendations</div>',
            '</div>',
            '<div class="stat-card">',
            '<div class="value">' + str(buy_count) + '</div>',
            '<div>Buy Signals</div>',
            '</div>',
            '<div class="stat-card">',
            '<div class="value">' + str(sell_count) + '</div>',
            '<div>Sell Signals</div>',
            '</div>',
            '<div class="stat-card">',
            '<div class="value">$' + str(config.CAPITAL) + '</div>',
            '<div>Trading Capital</div>',
            '</div>',
            '</div>',
        ]
        
        for rec in recommendations:
            action_class = 'buy' if rec.get('action') == 'BUY' else 'sell'
            conf = rec.get('confidence', 'LOW').lower()
            symbol = rec.get('symbol', 'N/A')
            action = rec.get('action', 'N/A')
            confidence = rec.get('confidence', 'LOW')
            reason = rec.get('reason', 'No reason provided')
            
            lines.append('<div class="rec-card ' + action_class + '">')
            lines.append('<div class="symbol">' + symbol + '</div>')
            lines.append('<div>')
            lines.append('<span class="action ' + action_class + '">' + action + '</span>')
            lines.append('<span class="confidence ' + conf + '">' + confidence + ' CONFIDENCE</span>')
            lines.append('</div>')
            
            # Show prices for both BUY and SELL signals
            entry = rec.get('entry_price', 0)
            target = rec.get('take_profit', 0)
            stop = rec.get('stop_loss', 0)
            rr = rec.get('risk_reward_ratio', 0)
            current = rec.get('current_price', 0)
            shares = rec.get('shares', 0)
            cost = rec.get('total_cost', 0)
            
            lines.append('<div class="prices">')
            lines.append('<div class="price-box"><div>Current</div><div class="value">$' + f"{current:.2f}" + '</div></div>')
            lines.append('<div class="price-box"><div>Entry</div><div class="value entry">$' + f"{entry:.2f}" + '</div></div>')
            lines.append('<div class="price-box"><div>Target</div><div class="value target">$' + f"{target:.2f}" + '</div></div>')
            lines.append('<div class="price-box"><div>Stop Loss</div><div class="value stop">$' + f"{stop:.2f}" + '</div></div>')
            lines.append('<div class="price-box"><div>R/R Ratio</div><div class="value">' + f"{rr:.1f}x" + '</div></div>')
            lines.append('</div>')
            
            if shares > 0:
                lines.append('<div class="prices">')
                lines.append('<div class="price-box"><div>Shares</div><div class="value">' + str(shares) + '</div></div>')
                lines.append('<div class="price-box"><div>Total Cost</div><div class="value">$' + f"{cost:.2f}" + '</div></div>')
                lines.append('<div class="price-box"><div>Risk Amount</div><div class="value">$' + f"{rec.get('risk_amount', 0):.2f}" + '</div></div>')
                lines.append('</div>')
            
            lines.append('<div class="reason">Reason: ' + reason + '</div>')
            lines.append('</div>')
        
        lines.append('</div>')
        lines.append('<div class="glossary" style="background:#1a1a2e;padding:20px;border-radius:15px;margin-top:30px;">')
        lines.append('<h2 style="color:#00d4ff;">Trading Terms Glossary</h2>')
        lines.append('<div style="display:grid;grid-template-columns:1fr 2fr;gap:10px;">')
        lines.append('<div><strong>Current</strong></div><div>Current market price right now</div>')
        lines.append('<div><strong>Entry</strong></div><div>Price at which you SHOULD enter the trade</div>')
        lines.append('<div><strong>Target</strong></div><div>Price where you take profit (exit with gain)</div>')
        lines.append('<div><strong>Stop Loss</strong></div><div>Price where you cut losses if trade goes wrong</div>')
        lines.append('<div><strong>R/R Ratio</strong></div><div>Risk/Reward - For every $1 risk, you gain this much</div>')
        lines.append('<div><strong>Confidence</strong></div><div>HIGH=Multiple indicators, MEDIUM=2+, LOW=1 indicator</div>')
        lines.append('</div>')
        lines.append('<h3 style="color:#ff4757;margin-top:20px;">For SELL Signals (Short Selling):</h3>')
        lines.append('<p>Sell at Entry, Buy back at Target for profit. If price rises to Stop Loss, buy back for loss.</p>')
        lines.append('<h3 style="color:#00d4ff;margin-top:15px;">For BUY Signals (Long Buying):</h3>')
        lines.append('<p>Buy at Entry, Sell at Target for profit. If price drops to Stop Loss, sell for loss.</p>')
        lines.append('</div>')
        lines.append('<div class="footer">')
        lines.append('<p>Warning: This is not financial advice. Trade at your own risk.</p>')
        lines.append('<p>Generated by Stock Trading Analysis System</p>')
        lines.append('</div>')
        lines.append('</body>')
        lines.append('</html>')
        
        html = '\n'.join(lines)
        
        filepath = config.ANALYSIS_REPORT_FILE
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath


def generate_recommendations_report(recommendations: List[Dict], market_data: Dict = None) -> Dict:
    """Generate all reports"""
    generator = ReportGenerator()
    
    json_path = generator.generate_json_report(recommendations)
    html_path = generator.generate_html_report(recommendations, market_data)
    
    return {
        'json': json_path,
        'html': html_path,
        'recommendations_count': len(recommendations)
    }