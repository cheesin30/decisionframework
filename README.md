# Multi-Strategy Alpaca Trading Bot

A Python bot that trades five instruments simultaneously through the
[Alpaca Markets](https://alpaca.markets) API using three strategy modules and
ATR-based risk management. Defaults to **paper trading**.

## Instruments & strategies

| Instrument | Strategy | Candles | Rules |
|---|---|---|---|
| SPY | Mean reversion | 15 min | Long/short beyond ±1.5σ of the 20-SMA; exit at the SMA |
| QQQ | Mean reversion | 15 min | Same, with a ±1.8σ band |
| BTC/USD | Momentum breakout | 1 h | Long on a 20-bar high break with ≥1.5× average volume; a confirmed breakdown exits (Alpaca crypto is long-only); 2×ATR trailing stop |
| GLD | Trend following | 4 h | Long on 50/200 EMA golden cross, short on death cross; 3×ATR trailing stop |
| USO | Trend following | 4 h | Same |

## Risk management

- **ATR sizing** — every position is sized so a 1 ATR (14-period, strategy
  timeframe) move against it equals 1% of account equity: quiet instruments
  get bigger positions, volatile ones smaller, risk stays constant.
- **Hard stop** — placed 1 ATR from the fill price, which caps every trade's
  loss at 1% of equity. Trailing stops (2×/3× ATR) only ever *tighten* the
  stop, so whichever stop is tighter wins and the 1% maximum always holds.
- **Notional cap** — a single position's notional can't exceed 50% of equity
  (`MAX_POSITION_NOTIONAL_PCT`), so a very quiet instrument can't absorb the
  whole account.
- **Correlation filter** — while SPY *and* QQQ are both long, new BTC/USD
  longs are blocked to avoid stacking risk-on exposure.

## Project layout

```
bot/
  strategies/
    base.py               # Strategy interface + Signal dataclass
    mean_reversion.py     # Strategy 1 (SPY, QQQ)
    momentum_breakout.py  # Strategy 2 (BTC/USD)
    trend_following.py    # Strategy 3 (GLD, USO)
  indicators.py           # SMA / EMA / stddev / Wilder ATR
  risk_manager.py         # Sizing, stops, correlation filter
  portfolio.py            # Positions, order execution, CSV logging
  main.py                 # Continuous loop / scheduler
  backtest.py             # Historical simulation of all strategies
config.py                 # All tunables (instruments, params, paths)
.env.example              # Template for API keys
requirements.txt
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then paste your Alpaca paper keys into .env
python -m bot.main
```

The loop wakes every 60 seconds: it checks stops against the latest trade
price, and evaluates each strategy once per newly completed candle (15 m /
1 h / 4 h). Equities are only traded while the market is open (checked via
Alpaca's clock endpoint); BTC/USD trades 24/7. API errors and disconnections
are caught and retried with exponential backoff, so a dropped connection or a
market closure never kills the process.

## Backtesting

```bash
python -m bot.backtest              # 6 months, $100k, backtest_results.png
python -m bot.backtest --months 12 --equity 50000 --output curve.png
```

Pulls historical bars from Alpaca for all five instruments at their live
timeframes (plus extra pre-window data so the 200-period EMA and ATR are
warmed up before the first tradable bar) and replays them through the *same*
strategy classes and risk manager the live bot uses. Fills happen at the
signal candle's close with 0.05% slippage per side and zero commission;
stops are honored intra-bar (gaps through a stop fill at the open);
positions still open at the end are force-closed on the final bar.

It reports, per instrument (independent runs) and for the combined portfolio
(shared equity, correlation filter active): total trades, win rate, average
win/loss, profit factor, maximum drawdown, Sharpe ratio (daily returns,
annualized), and total return. Any strategy with a negative Sharpe over the
window is flagged with the parameters to revisit. An equity-curve chart is
saved to `backtest_results.png`.

## Output files

- `trades.csv` — one row per entry and per exit: timestamp, instrument,
  direction, entry price, exit price, P&L, position size, plus the strategy
  and the signal reason.
- `daily_pnl.csv` — one row per (New York) calendar day: start equity, end
  equity, P&L, P&L %.
- `bot.log` — full runtime log.

## Design notes / deviations from the original spec

- **`alpaca-py` instead of `alpaca-trade-api`** — the legacy SDK was
  deprecated by Alpaca in 2023; `alpaca-py` is the maintained replacement.
- **Crypto shorts** — Alpaca doesn't support shorting crypto, so the BTC/USD
  breakdown signal closes the long rather than reversing short.
- **Stop interaction** — because sizing makes 1 ATR = 1% of equity, the hard
  1%-of-equity stop sits exactly 1 ATR from entry and is initially tighter
  than the 2×/3× ATR trails; the trail takes over once price moves far enough
  in the trade's favor.
- **Restart behavior** — on startup the bot adopts any existing broker
  positions in managed symbols; their stop is re-established from current ATR
  on the first candle close. Trend entries trigger on an actual EMA *cross*,
  so a restart mid-trend will not open a new trend position until the next
  cross.

## ⚠️ Disclaimer

This is example software, not financial advice. Test thoroughly on paper
trading before even considering real money.
