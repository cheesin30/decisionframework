"""Position tracking, order execution, and CSV trade/P&L logging."""

import csv
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

import config
from bot.strategies.base import LONG, SHORT

log = logging.getLogger("bot.portfolio")

TRADES_HEADER = ["timestamp", "instrument", "direction", "entry_price",
                 "exit_price", "pnl", "position_size", "event", "strategy",
                 "reason"]
DAILY_PNL_HEADER = ["date", "start_equity", "end_equity", "pnl", "pnl_pct"]


@dataclass
class Position:
    symbol: str
    strategy: str
    direction: str  # long / short
    qty: float
    entry_price: float
    entry_time: datetime
    atr_at_entry: float
    stop_price: Optional[float] = None
    trail_atr_mult: Optional[float] = None
    asset_class: str = "us_equity"


def _append_csv(path: Path, header, row) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(header)
        writer.writerow(row)


class Portfolio:
    """Owns open positions and routes orders through Alpaca."""

    def __init__(self, trading_client: TradingClient):
        self.trading = trading_client
        self.positions: Dict[str, Position] = {}

    # --- account -----------------------------------------------------------
    def equity(self) -> float:
        return float(self.trading.get_account().equity)

    def sync_from_broker(self, managed_symbols) -> None:
        """Adopt broker positions for managed symbols after a restart.

        The stop price is unknown at adoption; the first strategy evaluation
        re-establishes it from current ATR.
        """
        try:
            broker_positions = self.trading.get_all_positions()
        except APIError as exc:
            log.warning("Could not sync positions from broker: %s", exc)
            return
        # Broker reports crypto as e.g. BTCUSD while we key on BTC/USD.
        by_plain = {s.replace("/", ""): s for s in managed_symbols}
        for bp in broker_positions:
            symbol = by_plain.get(bp.symbol)
            if symbol is None:
                log.warning("Ignoring unmanaged broker position: %s", bp.symbol)
                continue
            direction = LONG if str(bp.side).endswith("long") else SHORT
            self.positions[symbol] = Position(
                symbol=symbol,
                strategy="adopted",
                direction=direction,
                qty=abs(float(bp.qty)),
                entry_price=float(bp.avg_entry_price),
                entry_time=datetime.now(timezone.utc),
                atr_at_entry=0.0,
                stop_price=None,
                asset_class="crypto" if "/" in symbol else "us_equity",
            )
            log.info("Adopted existing broker position: %s %s x%s @ %s",
                     symbol, direction, bp.qty, bp.avg_entry_price)

    # --- orders --------------------------------------------------------------
    def _submit_market(self, symbol: str, side: OrderSide, qty: float,
                       asset_class: str):
        tif = TimeInForce.GTC if asset_class == "crypto" else TimeInForce.DAY
        order = self.trading.submit_order(MarketOrderRequest(
            symbol=symbol, qty=qty, side=side, time_in_force=tif))
        deadline = time.monotonic() + config.ORDER_FILL_TIMEOUT
        while time.monotonic() < deadline:
            order = self.trading.get_order_by_id(order.id)
            status = str(order.status)
            if status.endswith("filled") and order.filled_avg_price is not None:
                return order
            if any(status.endswith(s) for s in ("canceled", "rejected", "expired")):
                log.error("Order for %s ended %s", symbol, status)
                return None
            time.sleep(1)
        log.error("Order for %s not filled within %ss; canceling",
                  symbol, config.ORDER_FILL_TIMEOUT)
        try:
            self.trading.cancel_order_by_id(order.id)
        except APIError as exc:
            log.warning("Cancel failed for %s: %s", symbol, exc)
        return None

    def open_position(self, symbol: str, asset_class: str, strategy_name: str,
                      direction: str, qty: float, atr: float,
                      stop_price: float, trail_atr_mult: Optional[float],
                      reason: str) -> Optional[Position]:
        side = OrderSide.BUY if direction == LONG else OrderSide.SELL
        order = self._submit_market(symbol, side, qty, asset_class)
        if order is None:
            return None
        entry_price = float(order.filled_avg_price)
        filled_qty = float(order.filled_qty)
        # Recompute the hard stop from the actual fill price rather than the
        # signal candle's close, so slippage never widens the risk past 1 ATR.
        stop_price = (entry_price - atr) if direction == LONG else (entry_price + atr)
        position = Position(
            symbol=symbol, strategy=strategy_name, direction=direction,
            qty=filled_qty, entry_price=entry_price,
            entry_time=datetime.now(timezone.utc), atr_at_entry=atr,
            stop_price=stop_price, trail_atr_mult=trail_atr_mult,
            asset_class=asset_class,
        )
        self.positions[symbol] = position
        _append_csv(config.TRADES_CSV, TRADES_HEADER, [
            datetime.now(timezone.utc).isoformat(), symbol, direction,
            f"{entry_price:.6f}", "", "", f"{filled_qty:.6f}", "entry",
            strategy_name, reason,
        ])
        log.info("OPENED %s %s x%.6f @ %.4f stop %.4f (%s)", direction, symbol,
                 filled_qty, entry_price, position.stop_price, reason)
        return position

    def close_position(self, symbol: str, reason: str) -> Optional[float]:
        """Close an open position at market. Returns realized P&L or None."""
        position = self.positions.get(symbol)
        if position is None:
            return None
        side = OrderSide.SELL if position.direction == LONG else OrderSide.BUY
        order = self._submit_market(symbol, side, position.qty,
                                    position.asset_class)
        if order is None:
            log.error("Failed to close %s — will retry next cycle", symbol)
            return None
        exit_price = float(order.filled_avg_price)
        sign = 1.0 if position.direction == LONG else -1.0
        pnl = (exit_price - position.entry_price) * position.qty * sign
        del self.positions[symbol]
        _append_csv(config.TRADES_CSV, TRADES_HEADER, [
            datetime.now(timezone.utc).isoformat(), symbol, position.direction,
            f"{position.entry_price:.6f}", f"{exit_price:.6f}", f"{pnl:.2f}",
            f"{position.qty:.6f}", "exit", position.strategy, reason,
        ])
        log.info("CLOSED %s %s x%.6f @ %.4f pnl %.2f (%s)", position.direction,
                 symbol, position.qty, exit_price, pnl, reason)
        return pnl

    # --- daily P&L -----------------------------------------------------------
    @staticmethod
    def log_daily_pnl(date_str: str, start_equity: float, end_equity: float) -> None:
        pnl = end_equity - start_equity
        pnl_pct = (pnl / start_equity * 100.0) if start_equity else 0.0
        _append_csv(config.DAILY_PNL_CSV, DAILY_PNL_HEADER, [
            date_str, f"{start_equity:.2f}", f"{end_equity:.2f}",
            f"{pnl:.2f}", f"{pnl_pct:.4f}",
        ])
        log.info("Daily P&L %s: %.2f (%.4f%%)", date_str, pnl, pnl_pct)
