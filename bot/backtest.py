"""Backtest all three strategies over historical Alpaca data.

Reuses the live strategy classes and RiskManager unchanged, so the simulation
exercises exactly the code the bot trades with:

- 6 months of bars per instrument at its live timeframe (15m SPY/QQQ,
  1h BTC/USD, 4h GLD/USO), plus extra pre-window data so slow indicators
  (the 200-period EMA especially) are fully warmed up before the first
  tradable bar.
- Fills at the signal candle's close with 0.05% slippage per side,
  zero commission (Alpaca). Matches the live bot, which submits a market
  order immediately after each candle closes.
- Stops are honored intra-bar: if a bar's range crosses the stop, the exit
  fills at the stop (or the open, when the bar gaps through it).
- Positions still open at the end of the window are force-closed on the
  final bar and included in the statistics.

Per instrument (independent $100k runs) and for the combined portfolio
(shared equity, correlation filter active) it reports: total trades, win
rate, average win/loss, profit factor, max drawdown, Sharpe ratio, and
total return; strategies with a negative Sharpe are flagged. An equity
curve chart is saved to backtest_results.png.

Run from the project root:  python -m bot.backtest [--months 6]
"""

import argparse
import logging
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd

import config
from bot.indicators import atr as atr_series
from bot.portfolio import Position
from bot.risk_manager import RiskManager
from bot.strategies.base import EXIT, LONG, SHORT
from bot.strategies.mean_reversion import MeanReversion
from bot.strategies.momentum_breakout import MomentumBreakout
from bot.strategies.trend_following import TrendFollowing

log = logging.getLogger("bot.backtest")

SLIPPAGE_PCT = 0.0005  # 0.05% per side
COMMISSION = 0.0       # Alpaca is commission-free

# Go-live gate: every strategy must clear both of these over the backtest
# window, or its parameters need adjusting before live trading.
MIN_SHARPE = 0.0
MAX_DRAWDOWN_LIMIT = 0.15

EQUITY_MINUTES_PER_DAY = 390
CRYPTO_MINUTES_PER_DAY = 1440

STRATEGY_CLASSES = {
    "mean_reversion": MeanReversion,
    "momentum_breakout": MomentumBreakout,
    "trend_following": TrendFollowing,
}

PARAM_HINTS = {
    "mean_reversion": "band width / SMA period",
    "momentum_breakout": "breakout period / volume multiple / trailing ATR mult",
    "trend_following": "EMA lengths / trailing ATR mult",
}


@dataclass
class TradeRecord:
    symbol: str
    strategy: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    reason: str


@dataclass
class Instrument:
    """One symbol + strategy + its historical bars."""
    symbol: str
    asset_class: str
    timeframe_minutes: int
    strategy: object
    bars: pd.DataFrame  # completed bars, oldest first, incl. warmup

    @property
    def eval_window(self) -> Optional[int]:
        # Trend following's EMAs need the full history to converge; the
        # rolling-window strategies only need their own lookback (this also
        # matches what the live bot fetches per cycle).
        if self.strategy.name == "trend_following":
            return None
        return int(self.strategy.min_bars * 1.3) + 5


@dataclass
class SimResult:
    label: str
    equity_curve: pd.Series
    trades: List[TradeRecord]
    initial_equity: float
    has_crypto: bool


# --------------------------------------------------------------------- data
def _timeframe(minutes: int):
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    if minutes < 60:
        return TimeFrame(minutes, TimeFrameUnit.Minute)
    return TimeFrame(minutes // 60, TimeFrameUnit.Hour)


def _warmup_days(cfg: dict, min_bars: int) -> float:
    """Calendar days of extra history needed to warm up the indicators."""
    tf = cfg["timeframe_minutes"]
    if cfg["asset_class"] == "crypto":
        bars_per_day = max(1, CRYPTO_MINUTES_PER_DAY // tf)
        return min_bars / bars_per_day + 2
    bars_per_day = max(1, EQUITY_MINUTES_PER_DAY // tf)
    return (min_bars / bars_per_day) * 1.6 + 7  # weekends and holidays


def fetch_history(start: datetime, end: datetime) -> Dict[str, pd.DataFrame]:
    """Pull bars for every configured instrument from Alpaca."""
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import (CryptoHistoricalDataClient,
                                        StockHistoricalDataClient)
    from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest

    stock = StockHistoricalDataClient(config.ALPACA_API_KEY,
                                      config.ALPACA_SECRET_KEY)
    crypto = CryptoHistoricalDataClient()
    feed = DataFeed.SIP if config.STOCK_DATA_FEED == "sip" else DataFeed.IEX

    out: Dict[str, pd.DataFrame] = {}
    for cfg in config.STRATEGY_CONFIGS:
        strategy_cls = STRATEGY_CLASSES[cfg["strategy"]]
        min_bars = strategy_cls(cfg["symbol"], cfg["params"]).min_bars
        fetch_start = start - timedelta(days=_warmup_days(cfg, min_bars))
        tf = _timeframe(cfg["timeframe_minutes"])
        log.info("Fetching %s %dm bars from %s ...", cfg["symbol"],
                 cfg["timeframe_minutes"], fetch_start.date())
        if cfg["asset_class"] == "crypto":
            req = CryptoBarsRequest(symbol_or_symbols=cfg["symbol"],
                                    timeframe=tf, start=fetch_start, end=end)
            df = crypto.get_crypto_bars(req).df
        else:
            req = StockBarsRequest(symbol_or_symbols=cfg["symbol"],
                                   timeframe=tf, start=fetch_start, end=end,
                                   feed=feed)
            df = stock.get_stock_bars(req).df
        if df is None or df.empty:
            raise RuntimeError(f"No historical data returned for {cfg['symbol']}")
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel(0)
        out[cfg["symbol"]] = df.sort_index()
        log.info("  %d bars for %s", len(df), cfg["symbol"])
    return out


def build_instruments(bars_map: Dict[str, pd.DataFrame]) -> List[Instrument]:
    instruments = []
    for cfg in config.STRATEGY_CONFIGS:
        cls = STRATEGY_CLASSES[cfg["strategy"]]
        instruments.append(Instrument(
            symbol=cfg["symbol"], asset_class=cfg["asset_class"],
            timeframe_minutes=cfg["timeframe_minutes"],
            strategy=cls(cfg["symbol"], cfg["params"]),
            bars=bars_map[cfg["symbol"]],
        ))
    return instruments


# ---------------------------------------------------------------- simulator
def _fill(price: float, side: str) -> float:
    """Apply per-side slippage: buys fill worse (higher), sells worse (lower)."""
    return price * (1 + SLIPPAGE_PCT) if side == "buy" else price * (1 - SLIPPAGE_PCT)


class Simulator:
    def __init__(self, instruments: List[Instrument], initial_equity: float,
                 correlation_filter: bool, trade_start: datetime, label: str):
        self.instruments = instruments
        self.initial_equity = initial_equity
        self.correlation_filter = correlation_filter
        self.trade_start = trade_start
        self.label = label
        self.risk = RiskManager()

        self.positions: Dict[str, Position] = {}
        self.realized = 0.0
        self.last_price: Dict[str, float] = {}
        self.trades: List[TradeRecord] = []
        self.equity_points: List[Tuple[datetime, float]] = []

    # --- accounting ---------------------------------------------------------
    def equity(self) -> float:
        unrealized = 0.0
        for pos in self.positions.values():
            price = self.last_price.get(pos.symbol, pos.entry_price)
            sign = 1.0 if pos.direction == LONG else -1.0
            unrealized += (price - pos.entry_price) * pos.qty * sign
        return self.initial_equity + self.realized + unrealized

    def _open(self, inst: Instrument, direction: str, price: float,
              atr_now: float, when: datetime, reason: str) -> None:
        fill = _fill(price, "buy" if direction == LONG else "sell")
        qty = self.risk.position_size(self.equity(), atr_now, fill,
                                      fractional=(inst.asset_class == "crypto"))
        if qty <= 0:
            return
        stop = self.risk.initial_stop(fill, atr_now, direction)
        self.positions[inst.symbol] = Position(
            symbol=inst.symbol, strategy=inst.strategy.name,
            direction=direction, qty=qty, entry_price=fill, entry_time=when,
            atr_at_entry=atr_now, stop_price=stop,
            trail_atr_mult=inst.strategy.trail_atr_mult,
            asset_class=inst.asset_class)

    def _close(self, symbol: str, price: float, when: datetime,
               reason: str) -> None:
        pos = self.positions.pop(symbol)
        fill = _fill(price, "sell" if pos.direction == LONG else "buy")
        sign = 1.0 if pos.direction == LONG else -1.0
        pnl = (fill - pos.entry_price) * pos.qty * sign - COMMISSION
        self.realized += pnl
        self.trades.append(TradeRecord(
            symbol=symbol, strategy=pos.strategy, direction=pos.direction,
            entry_time=pos.entry_time, exit_time=when,
            entry_price=pos.entry_price, exit_price=fill, qty=pos.qty,
            pnl=pnl, reason=reason))

    # --- per-bar logic --------------------------------------------------------
    def _check_stop(self, inst: Instrument, bar: pd.Series, bar_start: datetime,
                    close_time: datetime) -> None:
        pos = self.positions.get(inst.symbol)
        # Only bars that begin at/after entry can hit the stop.
        if pos is None or pos.stop_price is None or pos.entry_time > bar_start:
            return
        if pos.direction == LONG and bar["low"] <= pos.stop_price:
            # A gap through the stop fills at the open, not the stop.
            price = min(bar["open"], pos.stop_price)
            self._close(inst.symbol, price, close_time, "stop hit")
        elif pos.direction == SHORT and bar["high"] >= pos.stop_price:
            price = max(bar["open"], pos.stop_price)
            self._close(inst.symbol, price, close_time, "stop hit")

    def _handle_signal(self, inst: Instrument, window: pd.DataFrame,
                       atr_now: float, close_time: datetime) -> None:
        pos = self.positions.get(inst.symbol)
        signal = inst.strategy.evaluate(window, pos)
        if signal is None:
            return
        close = float(window["close"].iloc[-1])

        if signal.action == EXIT:
            if pos is not None:
                self._close(inst.symbol, close, close_time, signal.reason)
            return
        if pos is not None:
            if pos.direction == signal.action:
                return
            self._close(inst.symbol, close, close_time,
                        f"reversal: {signal.reason}")
        if self.correlation_filter and self.risk.correlation_blocks(
                inst.symbol, signal.action, self.positions):
            return
        self._open(inst, signal.action, close, atr_now, close_time,
                   signal.reason)

    def run(self) -> SimResult:
        # Merge every instrument's bars into one chronological event stream,
        # ordered by candle close time (start + timeframe).
        events: List[Tuple[datetime, Instrument, int]] = []
        for inst in self.instruments:
            delta = timedelta(minutes=inst.timeframe_minutes)
            for i, ts in enumerate(inst.bars.index):
                events.append((ts.to_pydatetime() + delta, inst, i))
        events.sort(key=lambda e: e[0])

        for close_time, inst, i in events:
            bar = inst.bars.iloc[i]
            bar_start = inst.bars.index[i].to_pydatetime()
            self._check_stop(inst, bar, bar_start, close_time)

            lo = 0 if inst.eval_window is None else max(0, i + 1 - inst.eval_window)
            window = inst.bars.iloc[lo:i + 1]
            if len(window) >= inst.strategy.min_bars:
                atr_now = float(atr_series(window, config.ATR_PERIOD).iloc[-1])
                pos = self.positions.get(inst.symbol)
                if pos is not None and not math.isnan(atr_now):
                    self.risk.update_trailing_stop(
                        pos, float(bar["close"]), atr_now,
                        inst.strategy.trail_atr_mult)
                if close_time >= self.trade_start and not math.isnan(atr_now):
                    self._handle_signal(inst, window, atr_now, close_time)

            self.last_price[inst.symbol] = float(bar["close"])
            # The curve covers only the tradable window, not indicator warmup.
            if close_time >= self.trade_start:
                self.equity_points.append((close_time, self.equity()))

        # Force-close whatever is still open on the final bar.
        if self.equity_points:
            final_time = self.equity_points[-1][0]
            for symbol in list(self.positions):
                self._close(symbol, self.last_price[symbol], final_time,
                            "end of backtest")
            self.equity_points.append((final_time, self.equity()))

        curve = pd.Series(dict(self.equity_points)).sort_index()
        has_crypto = any(x.asset_class == "crypto" for x in self.instruments)
        return SimResult(self.label, curve, self.trades,
                         self.initial_equity, has_crypto)


# ------------------------------------------------------------------- metrics
def compute_metrics(result: SimResult) -> dict:
    trades = result.trades
    curve = result.equity_curve
    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl <= 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)

    total_return = (curve.iloc[-1] / result.initial_equity - 1.0) if len(curve) else 0.0
    running_max = curve.cummax()
    max_dd = float((1.0 - curve / running_max).max()) if len(curve) else 0.0

    # Sharpe on daily equity returns, risk-free 0. Crypto trades every
    # calendar day; equities only trading days.
    sharpe = float("nan")
    if len(curve) > 2:
        daily = curve.resample("1D").last().dropna().pct_change().dropna()
        if len(daily) > 1 and daily.std() > 0:
            periods = 365 if result.has_crypto else 252
            sharpe = float(daily.mean() / daily.std() * math.sqrt(periods))

    return {
        "label": result.label,
        "trades": len(trades),
        "win_rate": (len(wins) / len(trades)) if trades else float("nan"),
        "avg_win": (gross_profit / len(wins)) if wins else 0.0,
        "avg_loss": (-gross_loss / len(losses)) if losses else 0.0,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0
                         else (float("inf") if gross_profit > 0 else float("nan")),
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "total_return": total_return,
    }


# --------------------------------------------------------------------- chart
# Colors from the validated reference palette (light mode): categorical slots
# in fixed order, recessive chrome.
SERIES_COLORS = ["#2a78d6", "#008300", "#e87ba4", "#eda100", "#1baf7a"]
SURFACE, INK, INK_2 = "#fcfcfb", "#0b0b0b", "#52514e"
MUTED, GRID, BASELINE = "#898781", "#e1e0d9", "#c3c2b7"


def plot_equity_curves(combined: SimResult,
                       per_instrument: List[SimResult],
                       path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    fmt_k = FuncFormatter(lambda v, _: f"${v / 1000:,.0f}k")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8.5), sharex=False,
                                   facecolor=SURFACE)

    def style(ax, title):
        ax.set_facecolor(SURFACE)
        ax.set_title(title, color=INK, fontsize=12, loc="left", pad=10)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.tick_params(colors=MUTED, labelsize=9)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(BASELINE)
        ax.yaxis.set_major_formatter(fmt_k)

    # Top: combined portfolio (single series — the title names it).
    style(ax1, "Combined portfolio — correlation filter active")
    ax1.plot(combined.equity_curve.index, combined.equity_curve.values,
             color=SERIES_COLORS[0], linewidth=2)
    ax1.axhline(combined.initial_equity, color=BASELINE, linewidth=0.8,
                linestyle="--")

    # Bottom: independent per-instrument runs.
    style(ax2, "Per-instrument equity — independent $%dk runs"
          % (per_instrument[0].initial_equity / 1000 if per_instrument else 0))
    ends = []
    for i, res in enumerate(per_instrument):
        color = SERIES_COLORS[i % len(SERIES_COLORS)]
        ax2.plot(res.equity_curve.index, res.equity_curve.values,
                 color=color, linewidth=2, label=res.label)
        ends.append([res.equity_curve.index[-1],
                     float(res.equity_curve.values[-1]), res.label, color])
    # Direct labels at the line ends (palette relief rule), nudged apart so
    # lines that finish at similar values don't produce overlapping text.
    if ends:
        lo, hi = ax2.get_ylim()
        min_gap = (hi - lo) * 0.035
        ends.sort(key=lambda e: e[1])
        for j in range(1, len(ends)):
            if ends[j][1] - ends[j - 1][1] < min_gap:
                ends[j][1] = ends[j - 1][1] + min_gap
        for ts, y, label, color in ends:
            ax2.annotate(f" {label}", (ts, y), color=color, fontsize=9,
                         va="center")
    ax2.axhline(per_instrument[0].initial_equity if per_instrument else 0,
                color=BASELINE, linewidth=0.8, linestyle="--")
    legend = ax2.legend(loc="upper left", frameon=False, fontsize=9)
    for text in legend.get_texts():
        text.set_color(INK_2)

    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    log.info("Equity curve chart saved to %s", path)


# -------------------------------------------------------------------- report
def _fmt(value, kind):
    if isinstance(value, float) and math.isnan(value):
        return "n/a"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "money":
        return f"${value:,.2f}"
    if kind == "ratio":
        return "inf" if value == float("inf") else f"{value:.2f}"
    return str(value)


def print_report(metrics: List[dict], strategy_by_label: Dict[str, object]) -> None:
    cols = [("Instrument", "label", None, 22), ("Trades", "trades", None, 7),
            ("Win rate", "win_rate", "pct", 9),
            ("Avg win", "avg_win", "money", 12),
            ("Avg loss", "avg_loss", "money", 12),
            ("PF", "profit_factor", "ratio", 6),
            ("Max DD", "max_drawdown", "pct", 8),
            ("Sharpe", "sharpe", "ratio", 7),
            ("Return", "total_return", "pct", 8)]
    header = "  ".join(name.ljust(w) for name, _, _, w in cols)
    print("\n" + "=" * len(header))
    print("BACKTEST RESULTS")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for m in metrics:
        row = []
        for _, key, kind, w in cols:
            val = m[key] if kind is None else _fmt(m[key], kind)
            row.append(str(val).ljust(w))
        print("  ".join(row))
    print("=" * len(header))

    # Go-live gate: flag any strategy with a negative Sharpe or a max
    # drawdown above the limit.
    flagged = False
    for m in metrics:
        issues = []
        if not math.isnan(m["sharpe"]) and m["sharpe"] < MIN_SHARPE:
            issues.append(f"negative Sharpe ({m['sharpe']:.2f})")
        if m["max_drawdown"] > MAX_DRAWDOWN_LIMIT:
            issues.append(f"max drawdown {m['max_drawdown'] * 100:.1f}% > "
                          f"{MAX_DRAWDOWN_LIMIT * 100:.0f}% limit")
        if not issues:
            continue
        flagged = True
        strat = strategy_by_label.get(m["label"])
        if strat is not None:
            print(f"\n  ⚠ {m['label']} ({strat.name}): {', '.join(issues)} — "
                  f"adjust {PARAM_HINTS[strat.name]} "
                  f"(current params: {strat.params})")
        else:
            print(f"\n  ⚠ {m['label']}: {', '.join(issues)}")
    if flagged:
        print("\nGO-LIVE CHECK: ✗ FAILED — fix the flagged strategies and "
              "re-run before switching ALPACA_PAPER to false.")
    else:
        print(f"\nGO-LIVE CHECK: ✓ PASSED — every strategy has Sharpe >= "
              f"{MIN_SHARPE:.0f} and max drawdown <= "
              f"{MAX_DRAWDOWN_LIMIT * 100:.0f}%.")


# ---------------------------------------------------------------------- main
def run_backtest(bars_map: Dict[str, pd.DataFrame], trade_start: datetime,
                 initial_equity: float, output_png: str,
                 metrics_csv: Optional[str] = "backtest_metrics.csv") -> List[dict]:
    """Run per-instrument and combined simulations on prefetched bars."""
    instruments = build_instruments(bars_map)

    per_results = []
    strategy_by_label = {}
    for inst in instruments:
        sim = Simulator([inst], initial_equity, correlation_filter=False,
                        trade_start=trade_start, label=inst.symbol)
        per_results.append(sim.run())
        strategy_by_label[inst.symbol] = inst.strategy

    combined = Simulator(instruments, initial_equity, correlation_filter=True,
                         trade_start=trade_start,
                         label="Combined portfolio").run()

    metrics = [compute_metrics(r) for r in per_results]
    metrics.append(compute_metrics(combined))
    plot_equity_curves(combined, per_results, output_png)
    if metrics_csv:
        pd.DataFrame(metrics).to_csv(metrics_csv, index=False)
        log.info("Metrics written to %s", metrics_csv)
    print_report(metrics, strategy_by_label)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--months", type=int, default=6,
                        help="Backtest window length in months (default 6)")
    parser.add_argument("--equity", type=float, default=100_000,
                        help="Starting equity per run (default 100000)")
    parser.add_argument("--output", default="backtest_results.png",
                        help="Equity curve chart path")
    parser.add_argument("--metrics-csv", default="backtest_metrics.csv",
                        help="Where to write the metrics table as CSV")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
        sys.exit("Missing ALPACA_API_KEY / ALPACA_SECRET_KEY — copy "
                 ".env.example to .env and fill in your keys (stock data "
                 "requires them; crypto does not).")

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30 * args.months)
    log.info("Backtesting %s -> %s (fills at signal-bar close, %.2f%% "
             "slippage/side, $%.0f commission)", start.date(), end.date(),
             SLIPPAGE_PCT * 100, COMMISSION)
    bars_map = fetch_history(start, end)
    run_backtest(bars_map, trade_start=start, initial_equity=args.equity,
                 output_png=args.output, metrics_csv=args.metrics_csv)


if __name__ == "__main__":
    main()
