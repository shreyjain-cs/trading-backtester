"""
DataHandler: fetches and stores historical price data.

WHY THIS IS ITS OWN CLASS (not just a pandas dataframe you pass around):
Later, when we build the event-driven loop, the Strategy component should
ONLY be able to see data up to "today" in the simulation — never a single
row further. If we just handed the Strategy the whole dataframe, it would
be very easy (and very tempting) to accidentally peek ahead, e.g. by
calling df['close'].rolling(50).mean() over the ENTIRE dataset, which
uses future prices to compute past averages in a way that wouldn't be
possible in real time.

By wrapping the data in a class that only exposes "bars up to the current
index," we make that mistake structurally hard to make, not just something
we have to remember not to do.
"""

import yfinance as yf
import pandas as pd


class DataHandler:
    def __init__(self, ticker: str, start: str, end: str):
        """
        ticker: e.g. 'AAPL'
        start, end: 'YYYY-MM-DD' strings
        """
        self.ticker = ticker
        raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)

        # yfinance sometimes returns MultiIndex columns for a single ticker
        # depending on version -- flatten it so we don't fight this later.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        raw = raw.reset_index()  # turn the Date index into a normal column
        raw.columns = [c.lower() for c in raw.columns]

        self.data = raw  # full dataframe, columns: date, open, high, low, close, volume
        self.current_index = 0  # this is our "clock" -- where we are in simulated time

    @classmethod
    def from_csv(cls, path: str, ticker: str = "UNKNOWN"):
        """
        Alternate constructor for loading from a CSV instead of hitting yfinance.
        Useful for testing offline, or for sharing a reproducible dataset with
        someone else so your results can be checked.
        Expects columns: date, open, high, low, close, volume
        """
        instance = cls.__new__(cls)  # build an empty instance without calling __init__
        instance.ticker = ticker
        df = pd.read_csv(path, parse_dates=["date"])
        df.columns = [c.lower() for c in df.columns]
        instance.data = df
        instance.current_index = 0
        return instance

    def total_bars(self) -> int:
        return len(self.data)

    def get_current_bar(self):
        """The single bar (row) 'now' -- the most recent data the Strategy is allowed to see."""
        return self.data.iloc[self.current_index]

    def get_bars_up_to_now(self) -> pd.DataFrame:
        """
        Everything from the start UP TO AND INCLUDING the current index.
        This is the key method: any Strategy logic (moving averages, etc.)
        must be computed from THIS, never from self.data directly.
        """
        return self.data.iloc[: self.current_index + 1]

    def advance(self) -> bool:
        """
        Move the clock forward one bar. Returns False when we've run out of data,
        which is how the main backtest loop knows to stop.
        """
        if self.current_index + 1 >= len(self.data):
            return False
        self.current_index += 1
        return True


if __name__ == "__main__":
    # On YOUR machine, with normal internet access, this is the real path:
    #   dh = DataHandler("AAPL", "2022-01-01", "2023-01-01")
    #
    # Here, we use the CSV loader so this runs without live network access:
    dh = DataHandler("AAPL", "2022-01-01", "2023-01-01")

    print(f"Loaded {dh.total_bars()} bars for {dh.ticker}")
    print(dh.data.head())

    print("\n--- Testing the 'clock' ---")
    print(f"Current bar (index {dh.current_index}):")
    print(dh.get_current_bar())

    print("\nAdvancing 5 bars...")
    for _ in range(5):
        dh.advance()
    print(f"Current bar (index {dh.current_index}):")
    print(dh.get_current_bar())

    print(f"\nget_bars_up_to_now() returns {len(dh.get_bars_up_to_now())} rows "
          f"(should be {dh.current_index + 1})")
