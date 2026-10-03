import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator


def generate_backtest_signals(df, strategy="swing"):
    signals = pd.Series(0, index=df.index)

    if strategy == "swing":
        ema20 = df["close"].ewm(span=20).mean()
        ema50 = df["close"].ewm(span=50).mean()
        rsi = RSIIndicator(df["close"], window=14).rsi()

        buy_cond = (ema20 > ema50) & (rsi > 55) & (rsi.shift(1) <= 55)
        sell_cond = (ema20 < ema50) | (rsi < 45)

        signals[buy_cond] = 1
        signals[sell_cond] = -1

    elif strategy == "momentum":
        roc = df["close"].pct_change(10)
        signals[roc > 0.05] = 1
        signals[roc < -0.03] = -1

    return signals


def run_backtest(price_df, signals, initial_capital=100000, fees=0.001, slippage=0.001):
    """
    Simple vectorized backtest (no external dependency).
    """
    df = price_df.copy().reset_index(drop=True)
    df["signal"] = signals.values

    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    equity_curve = []

    for i, row in df.iterrows():
        price = row["close"]
        sig = row["signal"]

        if sig == 1 and position == 0:
            position = capital / price
            entry_price = price
            capital = 0
        elif sig == -1 and position > 0:
            exit_price = price
            gross = position * exit_price
            cost = gross * (fees + slippage)
            capital = gross - cost
            pnl_pct = (exit_price - entry_price) / entry_price * 100
            trades.append(pnl_pct)
            position = 0

        current_equity = capital + (position * price if position > 0 else 0)
        equity_curve.append(current_equity)

    # Close open position at last price
    if position > 0:
        capital = position * df.iloc[-1]["close"]
        pnl_pct = (df.iloc[-1]["close"] - entry_price) / entry_price * 100
        trades.append(pnl_pct)

    equity = pd.Series(equity_curve)
    total_return = (capital / initial_capital - 1) * 100
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max * 100
    max_dd = drawdown.min()

    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    win_rate = (len(wins) / len(trades) * 100) if trades else 0

    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

    returns = equity.pct_change().dropna()
    sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

    return {
        "Total_Return_%": round(total_return, 2),
        "Sharpe_Ratio": round(sharpe, 2),
        "Max_Drawdown_%": round(max_dd, 2),
        "Win_Rate_%": round(win_rate, 2),
        "Total_Trades": len(trades),
        "Avg_Trade_%": round(np.mean(trades), 2) if trades else 0,
        "Profit_Factor": round(profit_factor, 2),
    }
