class MovingAverageCrossStrategy:
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, bars) -> str:
        """
        bars: dataframe of all data up to and including the current bar
              (comes from data_handler.get_bars_up_to_now())
        Returns "BUY", "SELL", or "HOLD".
        """
        # Q2: not enough data yet?
        if len(bars) < self.long_window + 1:
            return "HOLD"

        closes = bars["close"]

        # Today's two moving averages

        short_ma_today = closes.tail(self.short_window).mean()
        long_ma_today = closes.tail(self.long_window).mean()

        # Q3: yesterday's two moving averages

        closes_yesterday = closes.iloc[:-1]   # everything except the last row
        short_ma_yesterday = closes_yesterday.tail(self.short_window).mean()
        long_ma_yesterday = closes_yesterday.tail(self.long_window).mean()

        # Now compare
        if short_ma_yesterday < long_ma_yesterday and short_ma_today > long_ma_today:
            return "BUY"
        elif short_ma_yesterday > long_ma_yesterday and short_ma_today < long_ma_today:
            return "SELL"
        else:
            return "HOLD"