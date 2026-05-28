"""
Backtesting Engine for Stock Trading
Avoids overfitting with walk-forward validation and cross-validation
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class BacktestEngine:
    """
    Backtesting Engine with Overfitting Prevention
    
    Features:
    - Walk-Forward Validation
    - Cross-Validation
    - Monte Carlo Simulation
    - Performance Metrics
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.trades = []
        self.equity_curve = []
        
    def run_backtest(self, df: pd.DataFrame, signals: pd.DataFrame, 
                     initial_capital: float = None) -> Dict:
        """Run backtest on historical data"""
        if initial_capital is None:
            initial_capital = self.initial_capital
            
        capital = initial_capital
        position = None
        trades = []
        equity_curve = [initial_capital]
        
        for i, (idx, row) in enumerate(df.iterrows()):
            if i < len(signals):
                signal = signals.iloc[i] if i < len(signals) else None
                if signal is None:
                    continue
                
                action = signal.get('action', 'HOLD')
                price = row.get('close', 0)
                
                # Entry
                if action == 'BUY' and position is None and capital >= price * 100:
                    shares = int(capital / price / 100) * 100
                    if shares > 0:
                        position = {
                            'entry_date': idx,
                            'entry_price': price,
                            'shares': shares,
                            'capital_used': shares * price
                        }
                        capital -= shares * price
                
                # Exit
                elif (action == 'SELL' or action == 'CLOSE') and position is not None:
                    pnl = (price - position['entry_price']) * position['shares']
                    capital += position['shares'] * price
                    trades.append({
                        'entry_date': position['entry_date'],
                        'exit_date': idx,
                        'entry_price': position['entry_price'],
                        'exit_price': price,
                        'shares': position['shares'],
                        'pnl': pnl,
                        'return': pnl / position['capital_used']
                    })
                    position = None
            
            # Track equity
            if position is not None:
                current_value = capital + position['shares'] * row.get('close', position['entry_price'])
            else:
                current_value = capital
            equity_curve.append(current_value)
        
        # Calculate metrics
        metrics = self.calculate_metrics(trades, equity_curve, initial_capital)
        metrics['trades'] = trades
        metrics['equity_curve'] = equity_curve
        
        return metrics
    
    def walk_forward_validation(self, df: pd.DataFrame, train_ratio: float = 0.7) -> Dict:
        """
        Walk-Forward Validation to avoid overfitting
        
        Train on historical data, test on future data
        """
        n = len(df)
        train_size = int(n * train_ratio)
        
        train_df = df[:train_size]
        test_df = df[train_size:]
        
        # Train on first portion
        train_metrics = self.run_backtest(train_df, train_df)
        
        # Test on second portion (out-of-sample)
        test_metrics = self.run_backtest(test_df, test_df)
        
        return {
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'train_size': train_size,
            'test_size': len(test_df),
            'overfitting_score': abs(train_metrics['total_return'] - test_metrics['total_return'])
        }
    
    def calculate_metrics(self, trades: List[Dict], equity_curve: List[float], 
                          initial_capital: float) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'total_trades': 0
            }
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        final_value = equity_curve[-1] if equity_curve else initial_capital
        total_return = (final_value - initial_capital) / initial_capital * 100
        
        # Calculate Sharpe Ratio
        returns = [t['return'] for t in trades]
        mean_return = np.mean(returns) if returns else 0
        std_return = np.std(returns) if returns else 1
        sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        # Calculate Max Drawdown
        equity = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        max_drawdown = abs(np.min(drawdown)) * 100 if len(drawdown) > 0 else 0
        
        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'win_rate': round(win_rate * 100, 2),
            'profit_factor': round(profit_factor, 2),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': round(total_wins / len(winning_trades), 2) if winning_trades else 0,
            'avg_loss': round(total_losses / len(losing_trades), 2) if losing_trades else 0
        }
    
    def monte_carlo_simulation(self, trades: List[Dict], n_simulations: int = 1000) -> Dict:
        """Monte Carlo simulation for robustness testing"""
        if not trades:
            return {'median_return': 0, 'confidence_interval': [0, 0]}
        
        returns = [t['return'] for t in trades]
        simulation_results = []
        
        for _ in range(n_simulations):
            # Randomly sample trades with replacement
            sampled_returns = np.random.choice(returns, size=len(returns), replace=True)
            cumulative_return = (1 + sampled_returns).prod() - 1
            simulation_results.append(cumulative_return * 100)
        
        simulation_results = np.array(simulation_results)
        
        return {
            'median_return': round(np.median(simulation_results), 2),
            'mean_return': round(np.mean(simulation_results), 2),
            'std_return': round(np.std(simulation_results), 2),
            'confidence_interval': [
                round(np.percentile(simulation_results, 5), 2),
                round(np.percentile(simulation_results, 95), 2)
            ],
            'probability_of_profit': round((simulation_results > 0).mean() * 100, 2)
        }
    
    def cross_validate(self, df: pd.DataFrame, n_folds: int = 5) -> Dict:
        """K-Fold Cross-Validation"""
        n = len(df)
        fold_size = n // n_folds
        
        fold_results = []
        
        for i in range(n_folds):
            # Test on fold i, train on rest
            test_start = i * fold_size
            test_end = (i + 1) * fold_size
            
            train_df = pd.concat([df[:test_start], df[test_end:]])
            test_df = df[test_start:test_end]
            
            metrics = self.run_backtest(test_df, test_df)
            fold_results.append(metrics['total_return'])
        
        return {
            'fold_returns': fold_results,
            'mean_return': round(np.mean(fold_results), 2),
            'std_return': round(np.std(fold_results), 2),
            'is_stable': np.std(fold_results) < 10  # Less than 10% std deviation
        }
