"""Backtesting Engine for Intraday Trading Strategies"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000, risk_per_trade: float = 0.02):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, symbol: str, start_date: str, end_date: str, 
                     interval: str = "5m", use_stop_loss: bool = True,
                     atr_multiplier: float = 1.5) -> Dict:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty or len(df) < 100:
            return {'error': 'Insufficient data for backtesting'}
        
        self.trades = []
        self.equity_curve = [self.initial_capital]
        current_capital = self.initial_capital
        position = None
        trade_num = 0
        
        df = self._prepare_data(df)
        
        for i in range(50, len(df)):
            current_bar = df.iloc[i]
            current_price = current_bar['Close']
            current_time = current_bar.name
            
            if position is not None:
                if use_stop_loss and current_price <= position['stop_loss']:
                    trade_pnl = (position['stop_loss'] - position['entry']) * position['shares']
                    current_capital += trade_pnl
                    trade_num += 1
                    self.trades.append({
                        'trade_num': trade_num,
                        'entry_time': str(position['entry_time']),
                        'exit_time': str(current_time),
                        'entry_price': position['entry'],
                        'exit_price': position['stop_loss'],
                        'shares': position['shares'],
                        'pnl': trade_pnl,
                        'exit_reason': 'STOP_LOSS'
                    })
                    position = None
                elif current_price >= position['target']:
                    trade_pnl = (position['target'] - position['entry']) * position['shares']
                    current_capital += trade_pnl
                    trade_num += 1
                    self.trades.append({
                        'trade_num': trade_num,
                        'entry_time': str(position['entry_time']),
                        'exit_time': str(current_time),
                        'entry_price': position['entry'],
                        'exit_price': position['target'],
                        'shares': position['shares'],
                        'pnl': trade_pnl,
                        'exit_reason': 'TARGET_HIT'
                    })
                    position = None
                elif current_time.hour >= 15 and current_time.minute >= 30:
                    trade_pnl = (current_price - position['entry']) * position['shares']
                    current_capital += trade_pnl
                    trade_num += 1
                    self.trades.append({
                        'trade_num': trade_num,
                        'entry_time': str(position['entry_time']),
                        'exit_time': str(current_time),
                        'entry_price': position['entry'],
                        'exit_price': current_price,
                        'shares': position['shares'],
                        'pnl': trade_pnl,
                        'exit_reason': 'EOD_CLOSE'
                    })
                    position = None
            
            if position is None:
                signal = self._check_signal(df.iloc[:i+1])
                if signal == 'BUY':
                    risk_amount = current_capital * self.risk_per_trade
                    atr = current_bar['atr']
                    risk_per_share = atr * atr_multiplier
                    shares = int(risk_amount / risk_per_share)
                    
                    if shares > 0:
                        entry_price = current_price
                        stop_loss = entry_price - risk_per_share
                        target = entry_price + (risk_per_share * 2)
                        
                        position = {
                            'entry': entry_price,
                            'stop_loss': stop_loss,
                            'target': target,
                            'shares': shares,
                            'cost': shares * entry_price,
                            'entry_time': current_time
                        }
            
            self.equity_curve.append(current_capital)
        
        return self._calculate_metrics(symbol, start_date, end_date)
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        ema_12 = df['Close'].ewm(span=12).mean()
        ema_26 = df['Close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(14).mean()
        
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3
        df['vwap'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
        
        df['ema_9'] = df['Close'].ewm(span=9).mean()
        df['ema_21'] = df['Close'].ewm(span=21).mean()
        
        return df
    
    def _check_signal(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return 'HOLD'
        
        current = df.iloc[-1]
        current_time = current.name
        
        # TIME FILTER: Trade 9:30am-3pm EST (market hours)
        hour = current_time.hour if hasattr(current_time, 'hour') else 10
        if hour < 13 or hour > 20:  # 9:30am-4pm EST in UTC terms
            return 'HOLD'
        
        # VOLUME FILTER: Must have above-average volume
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_current = current['Volume']
        vol_ok = vol_current > vol_avg * 0.8  # 20% above average
        
        # RSI FILTER: Not overbought/oversold
        rsi_ok = 40 < current['rsi'] < 70
        
        # MACD FILTER: Bullish crossover or above signal
        macd_ok = current['macd'] > current['macd_signal']
        
        # VWAP FILTER: Price above VWAP
        vwap_ok = current['Close'] > current['vwap']
        
        # EMA FILTER: Price above EMAs
        ema_ok = current['Close'] > current['ema_9']
        
        # ATR FILTER: Stock must be liquid enough (ATR > $0.50)
        atr_ok = current['atr'] > 0.5
        
        # Count bullish conditions
        bullish_count = sum([rsi_ok, macd_ok, vwap_ok, ema_ok, vol_ok, atr_ok])
        
        # Require at least 4 conditions for BUY (relaxed from 6)
        if bullish_count >= 4:
            return 'BUY'
        elif bullish_count <= 2:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _calculate_metrics(self, symbol: str, start_date: str, end_date: str) -> Dict:
        if not self.trades:
            return {'symbol': symbol, 'start_date': start_date, 'end_date': end_date, 'error': 'No trades generated'}
        
        trades_df = pd.DataFrame(self.trades)
        total_trades = len(self.trades)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = abs(trades_df[trades_df['pnl'] < 0]['pnl'].mean()) if losing_trades > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        final_capital = self.initial_capital + total_pnl
        total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        profit_factor = abs(avg_win / avg_loss) if avg_loss > 0 else 0
        max_drawdown = self._calculate_max_drawdown()
        
        return {
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'trades': self.trades
        }
    
    def _calculate_max_drawdown(self) -> float:
        if not self.equity_curve:
            return 0
        peak = self.equity_curve[0]
        max_dd = 0
        for value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        return max_dd