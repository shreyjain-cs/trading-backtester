# trading-backtester

An event-driven backtesting engine built from scratch in Python — no `backtrader`, no `zipline` — designed to evaluate trading strategies under realistic constraints rather than idealized ones.

The goal was never to find a profitable strategy. It was to build infrastructure honest enough to tell me when one isn't.

## Headline finding: the end date decides the answer

The same strategy, the same asset, the same code. The only thing that changes is where the backtest stops.

**Measured to January 2022**, the moving-average crossover posts the best risk-adjusted return in the comparison:

| | Return | Sharpe | Max drawdown | Trades |
|---|---|---|---|---|
| **MA crossover** | 91.63% | **1.47** | −21.30% | 9 |
| Static 65/35 | 93.07% | 1.37 | −21.13% | 0 |
| Buy & hold | 143.24% | 1.36 | −31.41% | 0 |

**Measured twelve months later**, a static 60/40 stock/cash portfolio beats it on *both* return and drawdown, with no signals and no trades:

| | Return | Sharpe | Max drawdown | Trades |
|---|---|---|---|---|
| MA crossover | 47.31% | 0.68 | −25.00% | 18 |
| **Static 60/40** | **47.41%** | 0.63 | **−23.94%** | **0** |
| Buy & hold | 79.03% | 0.70 | −31.41% | 0 |

Nothing about the strategy changed. Only the reporting window did.

That sensitivity is the actual result of this project. Period selection is among the most common unreported degrees of freedom in published backtests, and this one shows how much work it can quietly do.

![Equity curves, 2020–2023](equity_curve_2020_2023.png)

## Matched-risk comparison

Comparing total returns across strategies with different risk levels isn't meaningful — any low-volatility strategy can be scaled up. The fair question is *how much return per unit of risk taken*, so the engine sweeps static stock/cash allocations and compares at matched drawdown.

**2020–2023** — the strategy's max drawdown was −25.00%:

| Allocation | Return | Sharpe | Max DD |
|---|---|---|---|
| 50% | 39.51% | 0.60 | −21.66% |
| 55% | 43.46% | 0.62 | −22.84% |
| **60%** | **47.41%** | 0.63 | **−23.94%** |
| **65%** | **51.35%** | 0.64 | **−24.95%** |
| 70% | 55.35% | 0.65 | −25.90% |
| 75% | 59.30% | 0.66 | −26.77% |
| 80% | 63.25% | 0.67 | −27.58% |

At −24.95% drawdown — effectively identical risk to the strategy's −25.00% — a static 65/35 portfolio returned **51.35% against the strategy's 47.31%**. The 60/40 row dominates outright: higher return *and* shallower drawdown.

**2020–2022** — the strategy's max drawdown was −21.30%:

| Allocation | Return | Sharpe | Max DD |
|---|---|---|---|
| 50% | 71.62% | 1.38 | −16.50% |
| 60% | 85.92% | 1.37 | −19.60% |
| **65%** | **93.07%** | 1.37 | **−21.13%** |
| 70% | 100.33% | 1.37 | −22.66% |
| 75% | 107.48% | 1.37 | −24.15% |

Here the gap narrows to 1.4 points (93.07% vs 91.63%), and the strategy holds the highest Sharpe in the table.

On that Sharpe gap: 1.47 vs 1.37 across roughly 500 trading days is about 1.5 standard errors. It is suggestive, not conclusive — the honest reading is "the strategy had the highest Sharpe in this window," not that it has a durable edge.

## What the engine does to avoid lying

Backtesting bugs are dangerous because they produce *better* results, so they don't announce themselves. Three structural defenses:

**1. The strategy cannot see the future.**
`DataHandler` maintains a `current_index` that acts as a simulation clock. Strategies receive data only through `get_bars_up_to_now()`, which slices to that index. A strategy computing `.tail(20).mean()` is therefore guaranteed to be averaging past data — the future isn't in the object it was handed.

**2. Orders fill at the next bar's open.**
A signal derived from today's close could not have been acted on today; the close is only known once the market has shut. The earliest realistic fill is the next session's open. Using that bar's high, low, or close would each be a subtler version of the same bias, since none are knowable at order entry.

**3. Transaction costs are built into the fill price.**
Buys fill at `price × (1 + cost_rate)`, sells at `price × (1 − cost_rate)`, defaulting to 0.1%. Position sizing is computed from the cost-adjusted price, so orders are sized against what will actually be paid. On the 2020–2023 run this cost 2.7 percentage points across 18 trades — not a rounding error.

## Architecture

Each component is independently testable and knows nothing about the others' internals.

```
DataHandler       Price data and the simulation clock.
                  Exposes only bars up to the current index.

Strategy          Receives bars, returns "BUY" / "SELL" / "HOLD".
                  Knows nothing about cash, positions, or execution.

ExecutionHandler  Turns a signal into a trade at a realistic price.
                  Owns position sizing and cost modeling.

Portfolio         Cash, shares, cost basis, equity curve.
                  Pure accounting — rejects what it can't afford.

metrics           Sharpe ratio and max drawdown from an equity curve.
```

Swapping strategies touches one line of the main loop. The engine doesn't care whether a signal came from a moving-average crossover or a trained model.

The loop's ordering is what enforces correctness:

```python
bars = dh.get_bars_up_to_now()      # 1. see only the past
signal = strat.generate_signal(bars)
if not dh.advance(): break           # 2. time moves forward
ex.execute(signal)                   # 3. fill at the new bar's open
pf.record_equity(...)                # 4. mark to market
```

## Usage

```bash
pip install yfinance pandas matplotlib
python backtest.py
```

Price data is fetched live from Yahoo Finance via `yfinance`; nothing is bundled. Change the ticker and date range on line 58 of `backtest.py`.

## Files

| File | Purpose |
|---|---|
| `data_handler.py` | Price data + simulation clock |
| `portfolio.py` | Cash, positions, cost basis, equity curve |
| `execution_handler.py` | Order filling, position sizing, transaction costs |
| `strategy.py` | Moving-average crossover signal generation |
| `metrics.py` | Sharpe ratio, max drawdown |
| `equity_curve.py` | Chart rendering |
| `backtest.py` | Main loop, benchmarks, allocation sweep |

## Known limitations

Deliberate simplifications, not oversights:

- **Single asset.** No allocation across multiple tickers.
- **All-in position sizing.** Every trade deploys the full account — maximizing both upside and ruin risk.
- **No short selling.** Long or flat only.
- **Idle cash earns nothing.** In reality it would sit in a money market fund earning the risk-free rate. For a strategy that holds cash a large fraction of the time, this systematically understates its performance, and the effect grows with interest rates.
- **Survivorship bias is sidestepped, not solved.** Testing a single currently-listed ticker avoids the problem rather than addressing it. A multi-asset version would need point-in-time index constituents.
- **Flat transaction costs.** Real spreads widen under volatility and vary with liquidity.
- **The allocation comparison is hindsight-informed.** The 60% and 65% rows were identified by looking at the results. In fairness, so were the strategy's 20/50 windows — those are convention, not derived from the data either. Both sides carry the same advantage, but it's worth stating.

## Planned

- Walk-forward validation, necessary before evaluating any trained model
- Multiple tickers and periods, to turn a single observation into evidence
- Fixed-fraction position sizing, to separate signal quality from sizing effects
- A test suite covering the portfolio accounting
