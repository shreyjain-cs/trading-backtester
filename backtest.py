from data_handler import DataHandler
from portfolio import Portfolio
from execution_handler import ExecutionHandler
from strategy import MovingAverageCrossStrategy

def buy_and_hold(data_handler, initial_cash=100_000):
    """
    What would initial_cash have become if we'd just bought
    at the very first bar's open and held to the last bar's close?
    """
    data = data_handler.data   # the full dataframe

    first_open = data.iloc[0]["open"]
    last_close = data.iloc[-1]["close"]

    shares = int(initial_cash / first_open)      # how many can we afford at first_open?
    leftover_cash = initial_cash - (shares * first_open) # whatever's left after buying

    return (shares * last_close) + leftover_cash       # value of those shares at last_close, plus leftover
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

    return pf


if __name__ == "__main__":
    ticker, start, end = "AAPL", "2020-01-01", "2023-01-01"
    pf = run_backtest(ticker, start, end)

    final_equity = pf.equity_curve[-1]["equity"]
    
    # Benchmark: what if we'd just bought and held?
    dh = DataHandler(ticker, start, end)
    bh_final = buy_and_hold(dh, initial_cash=pf.initial_cash)

    print(f"Starting cash:     ${pf.initial_cash:,.2f}")
    print(f"--- Strategy ---")
    print(f"Final equity:      ${final_equity:,.2f}")
    print(f"Total return:      {(final_equity / pf.initial_cash - 1) * 100:.2f}%")
    print(f"Trades made:       {len(pf.trade_log)}")
    print(f"--- Buy & Hold ---")
    print(f"Final equity:      ${bh_final:,.2f}")
    print(f"Total return:      {(bh_final / pf.initial_cash - 1) * 100:.2f}%")