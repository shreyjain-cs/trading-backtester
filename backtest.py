from data_handler import DataHandler
from portfolio import Portfolio
from execution_handler import ExecutionHandler
from strategy import MovingAverageCrossStrategy
from metrics import sharpe_ratio, max_drawdown
from equity_curve import plot_equity_curves

def static_allocation(data_handler, initial_cash=100_000, allocation=1.0):
    """
    Put `allocation` of the cash into the asset on day 1 and hold.
    The remainder sits idle. allocation=1.0 is plain buy-and-hold.
    """
    data = data_handler.data
    first_open = data.iloc[0]["open"]

    to_invest = initial_cash * allocation
    shares = int(to_invest / first_open)
    idle_cash = initial_cash - (shares * first_open)

    equity_curve = []
    for i in range(len(data)):
        row = data.iloc[i]
        equity = (shares * row["close"]) + idle_cash
        equity_curve.append({"date": row["date"], "equity": equity})

    return equity_curve


def buy_and_hold(data_handler, initial_cash=100_000):
    return static_allocation(data_handler, initial_cash, allocation=1.0)

def run_backtest(ticker, start, end, initial_cash=100_000):
    dh = DataHandler(ticker, start, end)
    pf = Portfolio(initial_cash=initial_cash)
    ex = ExecutionHandler(dh, pf)
    strat = MovingAverageCrossStrategy(short_window=20, long_window=50)

    while True:
        # 1. Strategy sees only data up to now
        bars = dh.get_bars_up_to_now()
        signal = strat.generate_signal(bars)

        # 2. Advance the clock -- if we're out of data, stop
        if not dh.advance():
            break

        # 3. Fill the order at the NEW current bar's open
        ex.execute(signal)

        # 4. Record equity using the new bar's close
        bar = dh.get_current_bar()
        pf.record_equity(bar["date"], bar["close"])

    return pf, dh


if __name__ == "__main__":
    ticker, start, end = "AAPL", "2020-01-01", "2023-01-01"
    pf, dh = run_backtest(ticker, start, end)

    final_equity = pf.equity_curve[-1]["equity"]
    bh_curve = buy_and_hold(dh, initial_cash=pf.initial_cash)
    bh_final = bh_curve[-1]["equity"]

    print(f"Starting cash:     ${pf.initial_cash:,.2f}")

    print(f"--- Strategy ---")
    print(f"Final equity:      ${final_equity:,.2f}")
    print(f"Total return:      {(final_equity / pf.initial_cash - 1) * 100:.2f}%")
    print(f"Sharpe ratio:      {sharpe_ratio(pf.equity_curve):.2f}")
    print(f"Max drawdown:      {max_drawdown(pf.equity_curve) * 100:.2f}%")
    print(f"Trades made:       {len(pf.trade_log)}")

    print(f"--- Buy & Hold ---")
    print(f"Final equity:      ${bh_final:,.2f}")
    print(f"Total return:      {(bh_final / pf.initial_cash - 1) * 100:.2f}%")
    print(f"Sharpe ratio:      {sharpe_ratio(bh_curve):.2f}")
    print(f"Max drawdown:      {max_drawdown(bh_curve) * 100:.2f}%")

    static_curve = static_allocation(dh, initial_cash=pf.initial_cash, allocation=0.75)
    static_60_curve = static_allocation(dh, initial_cash=pf.initial_cash, allocation=0.60)
    static_final = static_curve[-1]["equity"]

    print(f"--- Static 75/25 ---")
    print(f"Final equity:      ${static_final:,.2f}")
    print(f"Total return:      {(static_final / pf.initial_cash - 1) * 100:.2f}%")
    print(f"Sharpe ratio:      {sharpe_ratio(static_curve):.2f}")
    print(f"Max drawdown:      {max_drawdown(static_curve) * 100:.2f}%")
    print(f"--- Allocation sweep ---")
    for alloc in [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        curve = static_allocation(dh, initial_cash=pf.initial_cash, allocation=alloc)
        final = curve[-1]["equity"]
        ret = (final / pf.initial_cash - 1) * 100
        dd = max_drawdown(curve) * 100
        sh = sharpe_ratio(curve)
        print(f"  {alloc:.0%}:  return {ret:6.2f}%   Sharpe {sh:.2f}   maxDD {dd:7.2f}%")

    plot_equity_curves(
        {
            "MA crossover": pf.equity_curve,
            "Buy & hold":   bh_curve,
            "Static 60/40": static_60_curve,
        },
        title=f"{ticker} {start[:4]}–{end[:4]} — ${pf.initial_cash:,.0f} starting capital",
        outfile="equity_curve_2020_2023.png",
    )