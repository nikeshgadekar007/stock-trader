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
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intraday Trading Recommendations</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 15px; }}
        .header h1 {{ color: #00d4ff; font-size: 2.5em; }}
        .header p {{ color: #888; margin-top: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
        .stat-card {{ background: #1a1a2e; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-card .value {{ font-size: 2em; font-weight: bold; color: #00d4ff; }}
        .stat-card .label {{ color: #888; margin-top: 5px; }}
        .recommendations {{ display: grid; gap: 20px; }}
        .rec-card {{ background: #1a1a2e; border-radius: 15px; padding: 25px; border-left: 5px solid #00d4ff; }}
        .rec-card.sell {{ border-left-color: #ff4757; }}
        .rec-card .symbol {{ font-size: 2em; font-weight: bold; color: #fff; }}
        .rec-card .action {{ display: inline-block; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin-top: 10px; }}
        .rec-card .action.buy {{ background: #00d4ff; color: #000; }}
        .rec-card .action.sell {{ background: #ff4757; color: #fff; }}
        .rec-card .confidence {{ display: inline-block; padding: 5px 15px; border-radius: 20px; margin-left: 10px; }}
        .rec-card .confidence.high {{ background: #00ff88; color: #000; }}
        .rec-card .confidence.medium {{ background: #ffaa00; color: #000; }}
        .rec-card .confidence.low {{ background: #888; color: #fff; }}
        .prices {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-top: 20px; }}
        .price-box {{ background: #16213e; padding: 15px; border-radius: 10px; text-align: center; }}
        .price-box .label {{ color: #888; font-size: 0.9em; }}
        .price-box .value {{ font-size: 1.5em; font-weight: bold; margin-top: 5px; }}
        .price-box .entry {{ color: #00d4ff; }}
        .price-box .target {{ color: #00ff88; }}
        .price-box .stop {{ color: #ff4757; }}
        .reason {{ margin-top: 15px; padding: 15px; background: #16213e; border-radius: 10px; color: #aaa; }}
        .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📈 Intraday Trading Recommendations</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} HKT | US Market Analysis</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="value">{len(recommendations)}</div>
            <div class="label">Total Recommendations</div>
        </div>
        <div class="stat-card">
            <div class="value">{len([r for r in recommendations if r.get('action') == 'BUY'])}</div>
            <div class="label">Buy Signals</div>
        </div>
        <div class="stat-card">
            <div class="value">{len([r for r in recommendations if r.get('action') == 'SELL'])}</div>
            <div class="label">Sell Signals</div>
        </div>
        <div class="stat-card">
            <div class="value">${config.CAPITAL:,}</div>
            <div class="label">Trading Capital</div>
        </div>
    </div>
    
    <div class="recommendations">
"""
        
        for rec in recommendations:
            action_class = 'buy' if rec.get('action') == 'BUY' else 'sell'
            conf = rec.get('confidence', 'LOW').lower()
            
            html += f"""
        <div class="rec-card {action_class}">
            <div class="symbol">{rec.get('symbol', 'N/A')}</div>
            <div>
                <span class="action {action_class}">{rec.get('action', 'N/A')}</span>
                <span class="confidence {conf}">{rec.get('confidence', 'LOW')} CONFIDENCE</span>
            </div>
"""
            
            if rec.get('action') == 'BUY':
                html += f"""
            <div class="prices">
                <div class="price-box">
                    <div class="label">Entry Price</div>
                    <div class="value entry">${rec.get('entry_price', 0):.2f}</div>
                </div>
                <div class="price-box">
                    <div class="label">Target</div>
                    <div class="value target">${rec.get('take_profit', 0):.2f}</div>
                </div>
                <div class="price-box">
                    <div class="label">Stop Loss</div>
                    <div class="value stop">${rec.get('stop_loss', 0):.2f}</div>
                </div>
                <div class="price-box">
                    <div class="label">Risk/Reward</div>
                    <div class="value">{rec.get('risk_reward_ratio', 0):.1f}x</div>
                </div>
            </div>
"""
            
            html += f"""
            <div class="reason">📋 {rec.get('reason', 'No reason provided')}</div>
        </div>
"""
        
        html += """
    </div>
    
    <div class="footer">
        <p>⚠️ This is not financial advice. Trade at your own risk.</p>
        <p>Generated by Stock Trading Analysis System</p>
    </div>
</body>
</html>
"""
        
        filepath = config.ANALYSIS_REPORT_FILE
        with open(filepath, 'w') as f:
            f.write(html)
        
        return filepath


def generate_recommendations_report(recommendations: List[Dict], market_data: Dict = None) -> Dict:
    """Generate all reports"""
    generator = ReportGenerator()
    
    json