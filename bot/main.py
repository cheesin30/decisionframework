"""Trading bot entry point.

Runs a continuous loop that, every POLL_SECONDS:
  1. rolls the daily P&L log at the New York date change,
  2. checks every open position's stop against the latest trade price,
  3. for each strategy whose candle just closed, fetches completed bars,
     evaluates the strategy, and routes any signal through the risk manager.

Run from the project root:  python -m bot.main
"""

import logging
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd
from alpaca.common.exceptions import APIError
from alpaca.data.enums import DataFeed
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import (CryptoBarsRequest, CryptoLatestTradeRequest,
                                  StockBarsRequest, StockLatestTradeRequest)
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

import config
from bot.indicators import atr as atr_series
from bot.portfolio import Portfolio
from bot.risk_manager import RiskManager
from bot.strategies.base import EXIT, LONG, SHORT
from bot.strategies.mean_reversion import MeanReversion
from bot.strategies.momentum_breakout import MomentumBreakout
from bot.strategies.trend_following import TrendFollowing

from alpaca.trading.client import TradingClient

log = logging.getLogger("bot")

NY = ZoneInfo("America/New_York")

STRATEGY_CLASSES = {
    "mean_reversion": MeanReversion,
    "momentum_breakout": MomentumBreakout,
    "trend_following": TrendFollowing,
}

# Regular-session minutes per day, used to estimate how far back to fetch.
EQUITY_MINUTES_PER_DAY = 390
CRYPTO_MINUTES_PER_DAY = 1440


class ScheduledStrategy:
    """A strategy instance plus its bar-schedule bookkeeping."""

    def __init__(self, cfg: dict):
        cls = STRATEGY_CLASSES[cfg["strategy"]]
        self.strategy = cls(cfg["symbol"], cfg["params"])
        self.symbol = cfg["symbol"]
        self.asset_class = cfg["asset_class"]
        self.timeframe_minutes = cfg["timeframe_minutes"]
        self.last_bar_ts = None  # timestamp of the last bar we evaluated


class TradingBot:
    def __init__(self):
        self.trading = TradingClient(config.ALPACA_API_KEY,
                                     config.ALPACA_SECRET_KEY,
                                     paper=config.ALPACA_PAPER)
        self.stock_data = StockHistoricalDataClient(config.ALPACA_API_KEY,
                                                    config.ALPACA_SECRET_KEY)
        self.crypto_data = CryptoHistoricalDataClient()
        self.stock_feed = (DataFeed.SIP if config.STOCK_DATA_FEED == "sip"
                           else DataFeed.IEX)
        self.risk = RiskManager()
        self.portfolio = Portfolio(self.trading)
        self.scheduled = [ScheduledStrategy(c) for c in config.STRATEGY_CONFIGS]

        self._clock_open = False
        self._clock_checked_at = 0.0
        self._day = datetime.now(NY).date()
        self._day_start_equity = None

    # ------------------------------------------------------------------ data
    @staticmethod
    def _timeframe(minutes: int) -> TimeFrame:
        if minutes < 60:
            return TimeFrame(minutes, TimeFrameUnit.Minute)
        return TimeFrame(minutes // 60, TimeFrameUnit.Hour)

    def _lookback_start(self, s: ScheduledStrategy) -> datetime:
        need = int(s.strategy.min_bars * 1.3) + 5
        if s.asset_class == "crypto":
            bars_per_day = max(1, CRYPTO_MINUTES_PER_DAY // s.timeframe_minutes)
            days = need / bars_per_day + 2
        else:
            bars_per_day = max(1, EQUITY_MINUTES_PER_DAY // s.timeframe_minutes)
            trading_days = need / bars_per_day
            days = trading_days * 1.6 + 7  # weekends and holidays
        return datetime.now(timezone.utc) - timedelta(days=days)

    def fetch_bars(self, s: ScheduledStrategy):
        """Return completed bars for the strategy, oldest first, or None."""
        tf = self._timeframe(s.timeframe_minutes)
        start = self._lookback_start(s)
        if s.asset_class == "crypto":
            req = CryptoBarsRequest(symbol_or_symbols=s.symbol, timeframe=tf,
                                    start=start)
            df = self.crypto_data.get_crypto_bars(req).df
        else:
            req = StockBarsRequest(symbol_or_symbols=s.symbol, timeframe=tf,
                                   start=start, feed=self.stock_feed)
            df = self.stock_data.get_stock_bars(req).df
        if df is None or df.empty:
            return None
        if isinstance(df.index, pd.MultiIndex):
            df = df.droplevel(0)
        df = df.sort_index()
        # Drop the still-forming bar: a bar stamped t covers [t, t + timeframe).
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=s.timeframe_minutes)
        df = df[df.index <= cutoff]
        return df if not df.empty else None

    def latest_price(self, symbol: str, asset_class: str) -> float:
        if asset_class == "crypto":
            req = CryptoLatestTradeRequest(symbol_or_symbols=symbol)
            trade = self.crypto_data.get_crypto_latest_trade(req)[symbol]
        else:
            req = StockLatestTradeRequest(symbol_or_symbols=symbol,
                                          feed=self.stock_feed)
            trade = self.stock_data.get_stock_latest_trade(req)[symbol]
        return float(trade.price)

    # ----------------------------------------------------------------- clock
    def equity_market_open(self) -> bool:
        now = time.monotonic()
        if now - self._clock_checked_at > 30:
            self._clock_open = self.trading.get_clock().is_open
            self._clock_checked_at = now
        return self._clock_open

    # ----------------------------------------------------------------- stops
    def check_stops(self) -> None:
        for symbol, position in list(self.portfolio.positions.items()):
            if position.stop_price is None:
                continue
            if position.asset_class == "us_equity" and not self.equity_market_open():
                continue  # can't exit a closed market; re-check next cycle
            try:
                price = self.latest_price(symbol, position.asset_class)
            except APIError as exc:
                log.warning("Price check failed for %s: %s", symbol, exc)
                continue
            hit = (price <= position.stop_price if position.direction == LONG
                   else price >= position.stop_price)
            if hit:
                self.portfolio.close_position(
                    symbol, f"stop hit: price {price:.4f} vs stop "
                            f"{position.stop_price:.4f}")

    # ------------------------------------------------------------- daily pnl
    def roll_daily_pnl(self) -> None:
        today = datetime.now(NY).date()
        if self._day_start_equity is None:
            self._day_start_equity = self.portfolio.equity()
        if today != self._day:
            end_equity = self.portfolio.equity()
            self.portfolio.log_daily_pnl(self._day.isoformat(),
                                         self._day_start_equity, end_equity)
            self._day = today
            self._day_start_equity = end_equity

    # ------------------------------------------------------------- strategies
    def run_strategies(self) -> None:
        for s in self.scheduled:
            if s.asset_class == "us_equity" and not self.equity_market_open():
                continue
            try:
                bars = self.fetch_bars(s)
            except APIError as exc:
                log.warning("Bar fetch failed for %s: %s", s.symbol, exc)
                continue
            if bars is None or len(bars) < s.strategy.min_bars:
                got = 0 if bars is None else len(bars)
                log.debug("Not enough bars for %s (%d/%d)", s.symbol, got,
                          s.strategy.min_bars)
                continue
            last_ts = bars.index[-1]
            if s.last_bar_ts is not None and last_ts <= s.last_bar_ts:
                continue  # no new completed candle since the last evaluation
            s.last_bar_ts = last_ts
            self._evaluate(s, bars)

    def _evaluate(self, s: ScheduledStrategy, bars: pd.DataFrame) -> None:
        position = self.portfolio.positions.get(s.symbol)
        current_atr = atr_series(bars, config.ATR_PERIOD).iloc[-1]
        close = float(bars["close"].iloc[-1])

        # Ratchet the trailing stop on every completed candle. Adopted
        # positions (stop unknown after restart) get a stop here too.
        if position is not None:
            if position.stop_price is None and not math.isnan(current_atr):
                self.risk.update_trailing_stop(position, close, current_atr,
                                               position.trail_atr_mult or 1.0)
            elif s.strategy.trail_atr_mult is not None:
                self.risk.update_trailing_stop(position, close, current_atr,
                                               s.strategy.trail_atr_mult)

        signal = s.strategy.evaluate(bars, position)
        if signal is None:
            return
        log.info("Signal %s %s: %s", signal.action.upper(), s.symbol,
                 signal.reason)

        if signal.action == EXIT:
            if position is not None:
                self.portfolio.close_position(s.symbol, signal.reason)
            return

        # Entry (possibly reversing an opposite position first).
        if position is not None:
            if position.direction == signal.action:
                return  # already positioned this way
            if self.portfolio.close_position(s.symbol, f"reversal: {signal.reason}") is None:
                return  # close failed; don't stack a new position on top

        if self.risk.correlation_blocks(s.symbol, signal.action,
                                        self.portfolio.positions):
            log.info("Correlation filter blocked %s long on %s (SPY and QQQ "
                     "are both long)", signal.action, s.symbol)
            return

        try:
            equity = self.portfolio.equity()
        except APIError as exc:
            log.warning("Equity fetch failed, skipping entry on %s: %s",
                        s.symbol, exc)
            return
        qty = self.risk.position_size(equity, current_atr, close,
                                      fractional=(s.asset_class == "crypto"))
        if qty <= 0:
            log.info("Sized to zero for %s (equity %.2f, ATR %.4f) — skipping",
                     s.symbol, equity, current_atr)
            return
        stop = self.risk.initial_stop(close, current_atr, signal.action)
        self.portfolio.open_position(
            symbol=s.symbol, asset_class=s.asset_class,
            strategy_name=s.strategy.name, direction=signal.action, qty=qty,
            atr=current_atr, stop_price=stop,
            trail_atr_mult=s.strategy.trail_atr_mult, reason=signal.reason)

    # ------------------------------------------------------------------ loop
    def run(self) -> None:
        log.info("Starting bot (%s trading) with %d strategies",
                 "paper" if config.ALPACA_PAPER else "LIVE",
                 len(self.scheduled))
        self.portfolio.sync_from_broker([s.symbol for s in self.scheduled])
        consecutive_failures = 0
        while True:
            try:
                self.roll_daily_pnl()
                self.check_stops()
                self.run_strategies()
                consecutive_failures = 0
            except KeyboardInterrupt:
                log.info("Shutting down on user interrupt")
                return
            except Exception as exc:  # noqa: BLE001 — keep the loop alive
                consecutive_failures += 1
                backoff = min(300, 5 * 2 ** consecutive_failures)
                log.exception("Cycle failed (%d in a row), backing off %ds: %s",
                              consecutive_failures, backoff, exc)
                time.sleep(backoff)
                continue
            time.sleep(config.POLL_SECONDS)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(config.BOT_LOG)],
    )
    if not config.ALPACA_API_KEY or not config.ALPACA_SECRET_KEY:
        sys.exit("Missing ALPACA_API_KEY / ALPACA_SECRET_KEY — copy "
                 ".env.example to .env and fill in your keys.")
    TradingBot().run()


if __name__ == "__main__":
    main()
