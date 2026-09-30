class ExecutionHandler:
    def __init__(self, data_handler, portfolio, cost_rate: float = 0.001):
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.cost_rate = cost_rate

    def execute(self, signal: str):
        """
        signal is "BUY", "SELL", or "HOLD".
        Assumes the clock has ALREADY advanced to bar N+1 --
        so the current bar's open is our realistic fill price.
        """
        if signal == "HOLD":
            return

        bar = self.data_handler.get_current_bar()
        fill_price = bar["open"]
        date = bar["date"]

        if signal == "BUY":
            # 1. figure out how many shares you can afford
            buy_price = fill_price * (1 + self.cost_rate)
            shares = int(self.portfolio.cash / buy_price)
            
            if shares == 0:
                pass
            # 2. call the right Portfolio method
            else:
                self.portfolio.buy(date, buy_price, shares)

        elif signal == "SELL":
            # sell everything you're holding
            sell_price = fill_price * (1 - self.cost_rate)
            if self.portfolio.shares_held == 0:
                pass
            else:
                self.portfolio.sell(date, sell_price, self.portfolio.shares_held)
