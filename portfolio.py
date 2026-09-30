"""
Portfolio: tracks cash, holdings, and total equity as trades happen.

DESIGN PRINCIPLE: this class does NOT decide what to buy or sell.
It only records the consequences of buy/sell decisions made elsewhere
(by the Strategy, later). This separation means:
  - You can trust the accounting regardless of strategy quality
  - You can test the Portfolio math independently of any trading logic
  - Swapping strategies later never requires touching this file

Everything here is in terms of ONE ticker for now, to keep it simple.
We can extend to multiple tickers once the single-asset case is solid.
"""


class Portfolio:
    def __init__(self, initial_cash: float = 100_000.0):
        self.cash = initial_cash
        self.shares_held = 0
        self.initial_cash = initial_cash

        # A running log of every trade we execute -- essential for debugging
        # AND for computing performance metrics later (win rate, avg trade, etc.)
        self.trade_log = []

        # A running log of total equity at each point in time -- this is
        # what becomes your equity curve plot at the end.
        self.equity_curve = []

        self.cost_basis = 0

    def buy(self, date, price: float, shares: int):
        """
        Attempt to buy `shares` at `price`. Returns True if the trade
        happened, False if we didn't have enough cash (we never allow
        going into negative cash -- that's not how real trading works
        unless you're using margin, which we're deliberately not modeling yet).
        """
        cost = price * shares
        if cost > self.cash:
            return False  # not enough cash -- reject the trade

        self.cash -= cost
        self.shares_held += shares
        self.cost_basis = self.cost_basis + cost
        self.trade_log.append({
            "date": date, "action": "BUY", "price": price,
            "shares": shares, "cash_after": self.cash
        })
        return True

    def sell(self, date, price: float, shares: int):
        """
        Attempt to sell `shares` at `price`. Returns False if we don't
        hold enough shares to sell (no short-selling yet -- that's a
        deliberate simplification for now).
        """
        if shares > self.shares_held:
            return False  # can't sell what we don't own

        proceeds = price * shares
        self.cash += proceeds
        avg_cost_per_share = self.cost_basis/self.shares_held
        self.shares_held -= shares
        self.cost_basis -= (avg_cost_per_share * shares)
        self.trade_log.append({
            "date": date, "action": "SELL", "price": price,
            "shares": shares, "cash_after": self.cash
        })
        return True

    def total_equity(self, current_price: float) -> float:
        """
        Cash + market value of whatever shares we're holding.
        This is THE number that matters -- your account's total worth
        at this moment in time.
        """
        return self.cash + (self.shares_held * current_price)

    def record_equity(self, date, current_price: float):
        """
        Call this once per bar in the main loop -- this is how we build
        the equity curve we'll plot at the end.
        """
        equity = self.total_equity(current_price)
        self.equity_curve.append({"date": date, "equity": equity})
        return equity


if __name__ == "__main__":
    # Sanity check: simulate a tiny sequence of trades by hand and verify
    # the numbers make sense.
    p = Portfolio(initial_cash=10_000)

    print(f"Start: cash={p.cash}, shares={p.shares_held}")

    # Buy 10 shares at $100
    ok = p.buy(date="2022-01-01", price=100, shares=10)
    print(f"Bought 10 @ $100 -> success={ok}, cash={p.cash}, shares={p.shares_held}")

    # Price rises to $110 -- check unrealized equity
    equity = p.total_equity(current_price=110)
    print(f"Price now $110 -> total equity = {equity} (expect 9000 cash + 1100 shares = 10100)")

    # Try to buy more than we can afford
    ok = p.buy(date="2022-01-02", price=110, shares=1000)
    print(f"Tried to buy 1000 @ $110 (too expensive) -> success={ok} (expect False)")

    # Sell 5 shares at $110
    ok = p.sell(date="2022-01-03", price=110, shares=5)
    print(f"Sold 5 @ $110 -> success={ok}, cash={p.cash}, shares={p.shares_held}")

    # Try to sell more shares than we hold
    ok = p.sell(date="2022-01-04", price=110, shares=100)
    print(f"Tried to sell 100 shares (only hold 5) -> success={ok} (expect False)")

    print(f"\nFinal trade log ({len(p.trade_log)} trades):")
    for t in p.trade_log:
        print(f"  {t}")


def unrealized_pnl(self, current_price: float) -> float:
    current_value = self.shares_held * current_price
    return current_value - self.cost_basis
