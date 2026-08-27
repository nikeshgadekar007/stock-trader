"""
Walk-Forward Validator - Tests the 35-layer system on out-of-sample windows.

The problem: Most scoring systems are tuned to in-sample data and fail live.
The solution: Roll forward through history, train on past, validate on future.

Method:
  1. Fetch 3-5 years of daily data for a symbol
  2. Score every N days using only data UP TO that date
  3. If score >= threshold, simulate entry at next open
  4. Exit after holding_days
  5. Report per-window win rate, profit factor, max DD, Sharpe, regime perf
"""
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')
from typing import Dict, List
from analysis.adaptive_weights import get_adjusted_total


class WalkForwardValidator:
    """Validate the confluence scoring system using walk-forward analysis."""

    def __init__(self, slippage_pct=0.1, holding_days=10, score_threshold=270,
                 warmup_days=120, score_frequency=5, max_windows=30,
                 use_regime_weights=True):
        self.slippage_pct = slippage_pct
        self.holding_days = holding_days
        self.score_threshold = score_threshold
        self.warmup_days = warmup_days
        self.score_frequency = score_frequency
        self.max_windows = max_windows
        self.use_regime_weights = use_regime_weights

    def run(self, symbol: str, period: str = '3y', direction: str = 'long') -> Dict:
        """Run walk-forward validation on a single symbol."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=True)
            if df.empty or len(df) < self.warmup_days + self.holding_days + 20:
                return {'error': 'Insufficient data for ' + symbol}
        except Exception as e:
            return {'error': str(e)}

        trades = []
        eval_indices = df.index[self.warmup_days:]
        score_dates = eval_indices[::self.score_frequency]

        scored_count = 0
        for score_date in score_dates:
            if scored_count >= self.max_windows:
                break
            try:
                window_df = df.loc[:score_date]
                if len(window_df) < 50:
                    continue

                result = self._score_at_date(window_df, direction)
                if 'error' in result:
                    continue
                score = result['adjusted_total']
                regime = result.get('regime', 'UNKNOWN')

                if score < self.score_threshold:
                    continue

                entry_idx = df.index.get_loc(score_date)
                if entry_idx + 1 >= len(df):
                    continue
                entry_date = df.index[entry_idx + 1]
                entry_price = float(df['Open'].iloc[entry_idx + 1])
                entry_price *= (1 + self.slippage_pct / 200)

                exit_idx = min(entry_idx + self.holding_days, len(df) - 1)
                exit_date = df.index[exit_idx]
                exit_price = float(df['Close'].iloc[exit_idx])
                exit_price *= (1 - self.slippage_pct / 200)

                if direction == 'long':
                    pnl_pct = (exit_price - entry_price) / entry_price * 100
                else:
                    pnl_pct = (entry_price - exit_price) / entry_price * 100

                trades.append({
                    'entry_date': str(entry_date.date()),
                    'exit_date': str(exit_date.date()),
                    'entry_price': round(entry_price, 2),
                    'exit_price': round(exit_price, 2),
                    'score': round(score, 1),
                    'regime': regime,
                    'pnl_pct': round(pnl_pct, 2),
                    'direction': direction,
                    'win': pnl_pct > 0,
                })
                scored_count += 1
            except Exception:
                continue

        return self._compile_results(symbol, trades, direction)
    def _score_at_date(self, df: pd.DataFrame, direction: str) -> Dict:
        """Score using historical data only. Fast local scoring (no API calls)."""
        try:
            scores = self._fast_score(df, direction)
            regime = self._estimate_regime(df)
            if self.use_regime_weights:
                adjusted_total = get_adjusted_total(scores, regime)
            else:
                adjusted_total = sum(scores.values())
            return {'scores': scores, 'regime': regime,
                    'adjusted_total': adjusted_total, 'raw_total': sum(scores.values())}
        except Exception as e:
            return {'error': str(e)}

    def _fast_score(self, df: pd.DataFrame, direction: str) -> Dict[str, int]:
        """Fast local scoring using only price-based layers."""
        scores = {}
        if df.empty or len(df) < 50:
            return scores
        close = df['Close']
        current = float(close.iloc[-1])
        # Trend (30pts)
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1] if len(df) >= 50 else ma20
        ma200 = close.rolling(200).mean().iloc[-1] if len(df) >= 200 else ma50
        if current > ma20 > ma50 > ma200:
            scores['trend'] = 30 if direction == 'long' else 0
        elif current > ma20 > ma50:
            scores['trend'] = 25 if direction == 'long' else 5
        elif current < ma20 < ma50 < ma200:
            scores['trend'] = 30 if direction == 'short' else 0
        elif current < ma20 < ma50:
            scores['trend'] = 25 if direction == 'short' else 5
        else:
            scores['trend'] = 10
        # RSI momentum (10pts)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.inf)
        rsi = float(100 - (100 / (1 + rs.iloc[-1])))
        if 50 < rsi < 70 and direction == 'long':
            scores['momentum'] = 10
        elif 30 < rsi < 50 and direction == 'short':
            scores['momentum'] = 10
        elif rsi > 80 or rsi < 20:
            scores['momentum'] = 3
        else:
            scores['momentum'] = 6
        # ATR risk (10pts)
        tr = pd.concat([
            df['High'] - df['Low'],
            (df['High'] - close.shift()).abs(),
            (df['Low'] - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        atr_pct = atr / current * 100
        if atr_pct < 2:
            scores['atr_risk'] = 10
        elif atr_pct < 4:
            scores['atr_risk'] = 7
        else:
            scores['atr_risk'] = 4
        # Volume (10pts)
        vol_ratio = float(df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1])
        if vol_ratio > 1.5:
            scores['volume'] = 10
        elif vol_ratio > 1.0:
            scores['volume'] = 7
        elif vol_ratio < 0.5:
            scores['volume'] = 3
        else:
            scores['volume'] = 5
        # Breakout (10pts)
        high_20 = df['High'].rolling(20).max().iloc[-1]
        low_20 = df['Low'].rolling(20).min().iloc[-1]
        if current > high_20 * 0.99 and direction == 'long':
            scores['breakout'] = 10
        elif current < low_20 * 1.01 and direction == 'short':
            scores['breakout'] = 10
        else:
            scores['breakout'] = 5
        # S/R (15pts)
        support = df['Low'].rolling(50).min().iloc[-1]
        resistance = df['High'].rolling(50).max().iloc[-1]
        sr_dist = min(abs(current - support) / current * 100,
                       abs(current - resistance) / current * 100)
        if sr_dist < 2:
            scores['support_resistance'] = 15 if direction == 'long' else 8
        elif sr_dist < 5:
            scores['support_resistance'] = 10
        else:
            scores['support_resistance'] = 5
        # Candlestick bias (10pts)
        last_3 = df.tail(3)
        bullish_days = sum(1 for i in range(len(last_3))
                          if last_3['Close'].iloc[i] > last_3['Open'].iloc[i])
        if bullish_days >= 2 and direction == 'long':
            scores['candlestick'] = 10
        elif bullish_days <= 1 and direction == 'short':
            scores['candlestick'] = 10
        else:
            scores['candlestick'] = 5
        return scores

    def _estimate_regime(self, df: pd.DataFrame) -> str:
        """Rough regime estimate from price action alone."""
        try:
            if len(df) < 200:
                return 'UNKNOWN'
            ma200 = df['Close'].rolling(200).mean()
            slope = (ma200.iloc[-1] - ma200.iloc[-60]) / ma200.iloc[-60] * 100
            vol = df['Close'].pct_change().rolling(20).std().iloc[-1] * 100
            if vol > 4:
                return 'VOLATILE_SHOCK'
            elif slope > 2:
                return 'BULL_TREND'
            elif slope < -2:
                return 'BEAR_TREND'
            elif abs(slope) < 0.5:
                return 'RANGE_BOUND'
            else:
                return 'LOW_VOL_GRIND'
        except Exception:
            return 'UNKNOWN'

    def _compile_results(self, symbol: str, trades: List[Dict], direction: str) -> Dict:
        """Compile trades into summary statistics."""
        if not trades:
            return {'error': 'No trades generated. Lower score threshold.',
                    'symbol': symbol, 'trades': []}
        wins = [t for t in trades if t['win']]
        losses = [t for t in trades if not t['win']]
        wr = len(wins) / len(trades) * 100
        avg_w = float(np.mean([t['pnl_pct'] for t in wins])) if wins else 0
        avg_l = float(np.mean([abs(t['pnl_pct']) for t in losses])) if losses else 0
        expectancy = (wr / 100 * avg_w) - ((100 - wr) / 100 * avg_l)
        total_return = sum(t['pnl_pct'] for t in trades)
        gross_profit = sum(t['pnl_pct'] for t in wins)
        gross_loss = abs(sum(t['pnl_pct'] for t in losses))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        cum_pnl = np.cumsum([t['pnl_pct'] for t in trades])
        peak = np.maximum.accumulate(cum_pnl)
        dd = cum_pnl - peak
        max_dd = float(abs(dd.min())) if len(dd) > 0 else 0
        pnl_array = [t['pnl_pct'] for t in trades]
        sharpe = (float(np.mean(pnl_array)) / float(np.std(pnl_array)) * np.sqrt(252 / self.holding_days)) if len(pnl_array) > 1 and np.std(pnl_array) > 0 else 0
        regime_perf = {}
        for regime in ['BULL_TREND', 'BEAR_TREND', 'RANGE_BOUND', 'VOLATILE_SHOCK', 'LOW_VOL_GRIND']:
            regime_trades = [t for t in trades if t['regime'] == regime]
            if regime_trades:
                r_wr = sum(1 for t in regime_trades if t['win']) / len(regime_trades) * 100
                r_avg = float(np.mean([t['pnl_pct'] for t in regime_trades]))
                regime_perf[regime] = {'trades': len(regime_trades),
                                       'win_rate': round(r_wr, 1),
                                       'avg_pnl': round(r_avg, 2)}
        return {'symbol': symbol, 'direction': direction, 'period': 'walk-forward',
                'threshold': self.score_threshold, 'total_trades': len(trades),
                'wins': len(wins), 'losses': len(losses), 'win_rate': round(wr, 1),
                'avg_win_pct': round(avg_w, 2), 'avg_loss_pct': round(avg_l, 2),
                'expectancy_pct': round(expectancy, 2),
                'total_return_pct': round(total_return, 2),
                'profit_factor': round(pf, 2) if pf != float('inf') else 999,
                'max_drawdown_pct': round(max_dd, 2),
                'sharpe_ratio': round(sharpe, 2),
                'regime_performance': regime_perf, 'trades': trades}


if __name__ == '__main__':
    print('Walk-Forward Validator - testing AAPL long')
    v = WalkForwardValidator(score_threshold=70, holding_days=10, max_windows=30)
    result = v.run('AAPL', period='3y', direction='long')
    if 'error' in result:
        print('Error: ' + result['error'])
    else:
        print("\n=== " + result['symbol'] + " (" + result['direction'] + ") ===")
        print("Trades: " + str(result['total_trades']))
        print("Win rate: " + str(result['win_rate']) + "%")
        print("Expectancy: " + str(result['expectancy_pct']) + "%")
        print("Profit factor: " + str(result['profit_factor']))
        print("Max drawdown: " + str(result['max_drawdown_pct']) + "%")
        print("Sharpe: " + str(result['sharpe_ratio']))
        print("\nRegime performance:")
        for r, p in result['regime_performance'].items():
            print("  " + r + ": " + str(p['trades']) + " trades, " + str(p['win_rate']) + "% WR, " + str(p['avg_pnl']) + "% avg")
