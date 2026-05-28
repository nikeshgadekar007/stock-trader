"""
Risk Management Calculator for Stock Trading
Position sizing, stop loss, and risk-reward calculations
"""

import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class TradeSetup:
    """Trading setup parameters"""
    symbol: str
    entry_price: float
    stop_loss: float
    target_price: float
    account_size: float = 10000
    risk_percent: float = 1.0  # Risk 1% of account per trade

@dataclass
class PositionSize:
    """Calculated position size"""
    shares: int
    position_value: float
    risk_amount: float
    risk_percent: float
    reward_amount: float
    risk_reward_ratio: float

def calculate_position_size(setup: TradeSetup) -> PositionSize:
    """Calculate optimal position size based on risk management rules"""
    
    # Calculate risk per share
    risk_per_share = abs(setup.entry_price - setup.stop_loss)
    
    # Calculate risk amount based on account percentage
    risk_amount = setup.account_size * (setup.risk_percent / 100)
    
    # Calculate number of shares
    shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
    
    # Calculate position value
    position_value = shares * setup.entry_price
    
    # Calculate reward
    reward_per_share = abs(setup.target_price - setup.entry_price)
    reward_amount = shares * reward_per_share
    
    # Calculate risk-reward ratio
    risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
    
    return PositionSize(
        shares=shares,
        position_value=position_value,
        risk_amount=risk_amount,
        risk_percent=setup.risk_percent,
        reward_amount=reward_amount,
        risk_reward_ratio=risk_reward_ratio
    )

def calculate_kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> Dict:
    """Calculate Kelly Criterion for position sizing"""
    if avg_loss == 0:
        return {'kelly_percent': 0, 'kelly_fraction': 'N/A', 'recommendation': 'Invalid'}
    
    win_loss_ratio = avg_win / avg_loss
    b = win_loss_ratio  # Odds received
    p = win_rate  # Probability of winning
    q = 1 - p  # Probability of losing
    
    # Kelly formula: f* = (bp - q) / b
    kelly = (b * p - q) / b
    
    # Cap Kelly at reasonable levels (max 25%)
    kelly = min(max(kelly, 0), 0.25)
    
    # Use half-Kelly for more conservative betting
    half_kelly = kelly / 2
    
    if kelly < 0:
        recommendation = "Don't trade - negative edge"
    elif kelly < 0.1:
        recommendation = "Very small position sizes"
    elif kelly < 0.2:
        recommendation = "Moderate position sizes"
    else:
        recommendation = "Large position sizes possible"
    
    return {
        'kelly_percent': kelly * 100,
        'half_kelly_percent': half_kelly * 100,
        'win_loss_ratio': win_loss_ratio,
        'win_rate': win_rate,
        'recommendation': recommendation
    }

def calculate_max_drawdown(equity_curve: list) -> Dict:
    """Calculate maximum drawdown from equity curve"""
    if not equity_curve:
        return {'max_drawdown': 0, 'max_drawdown_percent': 0}
    
    peak = equity_curve[0]
    max_dd = 0
    max_dd_percent = 0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        
        drawdown = peak - value
        drawdown_percent = (drawdown / peak) * 100 if peak > 0 else 0
        
        if drawdown > max_dd:
            max_dd = drawdown
            max_dd_percent = drawdown_percent
    
    return {
        'max_drawdown': max_dd,
        'max_drawdown_percent': max_dd_percent
    }

def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe Ratio"""
    if not returns or len(returns) < 2:
        return 0
    
    import numpy as np
    returns_array = np.array(returns)
    
    avg_return = np.mean(returns_array)
    std_return = np.std(returns_array)
    
    if std_return == 0:
        return 0
    
    sharpe = (avg_return - risk_free_rate) / std_return
    return sharpe

def calculate_var(returns: list, confidence: float = 0.95) -> Dict:
    """Calculate Value at Risk"""
    if not returns:
        return {'var_absolute': 0, 'var_percent': 0}
    
    import numpy as np
    returns_array = np.array(returns)
    
    var = np.percentile(returns_array, (1 - confidence) * 100)
    var_percent = abs(var) * 100
    
    return {
        'var_absolute': abs(var) * len(returns),
        'var_percent': var_percent,
        'confidence': confidence
    }

def get_risk_assessment(trade_setup: TradeSetup) -> Dict:
    """Get comprehensive risk assessment for a trade"""
    
    position = calculate_position_size(trade_setup)
    
    # Calculate risk metrics
    risk_reward = position.reward_amount / position.risk_amount if position.risk_amount > 0 else 0
    
    # Risk grades
    if risk_reward >= 3:
        risk_grade = 'A+'
        risk_description = 'Excellent risk-reward'
    elif risk_reward >= 2:
        risk_grade = 'A'
        risk_description = 'Good risk-reward'
    elif risk_reward >= 1.5:
        risk_grade = 'B'
        risk_description = 'Acceptable risk-reward'
    elif risk_reward >= 1:
        risk_grade = 'C'
        risk_description = 'Marginal risk-reward'
    else:
        risk_grade = 'D'
        risk_description = 'Poor risk-reward - avoid'
    
    # Position size assessment
    position_percent = (position.position_value / trade_setup.account_size) * 100
    
    if position_percent > 20:
        size_assessment = 'Very large - consider reducing'
    elif position_percent > 10:
        size_assessment = 'Large but acceptable'
    elif position_percent > 5:
        size_assessment = 'Moderate position'
    else:
        size_assessment = 'Small position'
    
    return {
        'trade_setup': {
            'symbol': trade_setup.symbol,
            'entry': trade_setup.entry_price,
            'stop': trade_setup.stop_loss,
            'target': trade_setup.target_price
        },
        'position_size': {
            'shares': position.shares,
            'value': position.position_value,
            'percent_of_account': position_percent
        },
        'risk_metrics': {
            'risk_amount': position.risk_amount,
            'reward_amount': position.reward_amount,
            'risk_reward_ratio': risk_reward
        },
        'assessment': {
            'grade': risk_grade,
            'description': risk_description,
            'position_assessment': size_assessment
        }
    }

def calculate_daily_risk(account_size: float, daily_risk_percent: float = 2.0) -> Dict:
    """Calculate daily risk limits"""
    daily_risk_amount = account_size * (daily_risk_percent / 100)
    
    # Max loss per trade (assuming 2 trades per day)
    max_loss_per_trade = daily_risk_amount / 2
    
    return {
        'account_size': account_size,
        'daily_risk_percent': daily_risk_percent,
        'daily_risk_amount': daily_risk_amount,
        'max_loss_per_trade': max_loss_per_trade,
        'max_trades_per_day': 2
    }

if __name__ == "__main__":
    # Example usage
    setup = TradeSetup(
        symbol='AAPL',
        entry_price=150.00,
        stop_loss=147.00,
        target_price=159.00,
        account_size=10000,
        risk_percent=1.0
    )
    
    result = get_risk_assessment(setup)
    print(f"\nRisk Assessment for {result['trade_setup']['symbol']}:")
    print(f"Grade: {result['assessment']['grade']} - {result['assessment']['description']}")
    print(f"Position: {result['position_size']['shares']} shares (${result['position_size']['value']:.2f})")
    print(f"Risk-Reward: {result['risk_metrics']['risk_reward_ratio']:.2f}")