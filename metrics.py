import pandas as pd
import math

def daily_returns(equity_curve) -> pd.Series:

    equities = pd.Series([point["equity"] for point in equity_curve])

    returns = []

    for i in range(1,len(equities)):
        today = equities.iloc[i]
        yesterday = equities.iloc[i-1]
        r = (today - yesterday)/yesterday
        returns.append(r)

    return pd.Series(returns)

def sharpe_ratio(equity_curve, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:

    returns = daily_returns(equity_curve)

    rf_daily = risk_free_rate / periods_per_year

    excess = returns - rf_daily

    mean_excess = excess.mean()
    std_excess = excess.std()

    return (mean_excess/std_excess) * math.sqrt(periods_per_year)

def max_drawdown(equity_curve) -> float:
    """
    Largest peak-to-trough decline, as a negative decimal.
    -0.25 means the account fell 25% below its prior high.
    """
    peak = equity_curve[0]["equity"]
    max_dd = 0.0

    for point in equity_curve:
        equity = point["equity"]
        if equity > peak:
            peak = equity
        gap = (equity - peak)/peak
        if gap < max_dd:
            max_dd = gap
    return max_dd