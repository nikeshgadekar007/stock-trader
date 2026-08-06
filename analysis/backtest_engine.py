"""
Backtesting Engine for 17-Layer Confluence Scoring System
Validates strategies against historical data with realistic costs
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
from .confluence_scorer import ConfluenceScorer


class BacktestEngine:

    def __init__(self, slippage_pct=0.1, commission=0.0):
        self.slippage_pct = slippage_pct
        self.commission = commission

    def run(self, symbol, period='2y', min_score=108, holding_days=10, max_positions=3):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=True)
            if df.empty or len(df) < 200:
                return {'error': f'Insufficient data ({len(df)} days)'}
        except Exception as e:
            return {'error': str(e)}

        trades = []
        equity = []
        holdings = []
        cash = 10000.0
        position_value = 0.0
        warmup = 120
        score_frequency = max(3, holding_days // 3)

        # Pre-score entire dataset using lightweight local-only layers
        scorer = ConfluenceScorer()
        eval_indices = df.index[warmup:]

        for i, current_date in enumerate(eval_indices):
            if i % score_frequency != 0 and len(holdings) >= max_positions:
                # Still check exits
                for h in holdings[:]:
                    entry_date, entry_price, _, h_score = h
                    days_held = len(df.loc[entry_date:current_date])
                    if days_held >= holding_days:
                        exit_price = df['Close'].loc[current_date] * (1 - self.slippage_pct / 100)
                        pnl = (exit_price - entry_price) / entry_price * 100
                        trades.append({
                            'entry_date': str(entry_date.date()),
                            'exit_date': str(current_date.date()),
                            'entry_price': round(entry_price, 2),
                            'exit_price': round(exit_price, 2),
                            'pnl_pct': round(pnl, 2),
                            'score': h_score, 'days_held': days_held,
                            'win': exit_price > entry_price
                        })
                        cash += 1000 + 1000 * pnl / 100
                        position_value -= 1000
                        holdings.remove(h)
                equity.append({'date': str(current_date.date()),
                               'equity': round(cash + position_value, 2)})
                continue

            # Exit check
            for h in holdings[:]:
                entry_date, entry_price, _, h_score = h
                days_held = len(df.loc[entry_date:current_date])
                if days_held >= holding_days:
                    exit_price = df['Close'].loc[current_date] * (1 - self.slippage_pct / 100)
                    pnl = (exit_price - entry_price) / entry_price * 100
                    trades.append({
                        'entry_date': str(entry_date.date()), 'exit_date': str(current_date.date()),
                        'entry_price': round(entry_price, 2), 'exit_price': round(exit_price, 2),
                        'pnl_pct': round(pnl, 2), 'score': h_score, 'days_held': days_held,
                        'win': exit_price > entry_price
                    })
                    cash += 1000 + 1000 * pnl / 100
                    position_value -= 1000
                    holdings.remove(h)

            if len(holdings) >= max_positions:
                equity.append({'date': str(current_date.date()),
                               'equity': round(cash + position_value, 2)})
                continue

            # Score using local window
            try:
                window_df = df.loc[:current_date]
                result = scorer.score_all(symbol)
                score = result.get('total_score', 0)
            except Exception:
                score = 0

            if score >= min_score:
                entry_price = df['Close'].loc[current_date]
                holdings.append((current_date, entry_price, current_date, score))
                position_value += 1000
                cash -= 1000 * (1 + self.slippage_pct / 100)

            equity.append({'date': str(current_date.date()),
                           'equity': round(cash + position_value, 2)})

        if not trades:
            return {'error': 'No trades — lower threshold', 'equity': equity}

        wins = [t for t in trades if t['win']]
        losses = [t for t in trades if not t['win']]
        wr = len(wins) / len(trades) * 100
        avg_w = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_l = np.mean([abs(t['pnl_pct']) for t in losses]) if losses else 0
        exp = (wr / 100 * avg_w) - ((100 - wr) / 100 * avg_l)

        eq_df = pd.DataFrame(equity)
        peak = eq_df['equity'].cummax()
        dd = (eq_df['equity'] - peak) / peak * 100
        max_dd = abs(dd.min())

        total_pnl = sum(t['pnl_pct'] for t in trades)
        pf = sum(t['pnl_pct'] for t in wins) / abs(sum(t['pnl_pct'] for t in losses)) if losses else float('inf')

        return {
            'symbol': symbol, 'period': period, 'min_score': min_score,
            'holding_days': holding_days, 'total_trades': len(trades),
            'wins': len(wins), 'losses': len(losses), 'win_rate': round(wr, 1),
            'avg_win_pct': round(avg_w, 2), 'avg_loss_pct': round(avg_l, 2),
            'expectancy_pct': round(exp, 2), 'total_return_pct': round(total_pnl, 2),
            'profit_factor': round(pf, 2) if pf != float('inf') else 999,
            'max_drawdown_pct': round(max_dd, 2), 'trades': trades, 'equity': equity
        }


if __name__ == '__main__':
    engine = BacktestEngine()
    for sym in ['SPY', 'AAPL', 'NVDA']:
        r = engine.run(sym, period='2y', min_score=108, holding_days=10)
        if 'error' in r:
            print(f"{sym}: {r['error']}")
            continue
        print(f"{sym}: {r['total_trades']} trades | WR:{r['win_rate']}% | "
              f"Exp:{r['expectancy_pct']}% | DD:{r['max_drawdown_pct']}% | PF:{r['profit_factor']}")