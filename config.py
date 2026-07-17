"""Central configuration for the trading bot.

API credentials come from a .env file (see .env.example). Everything else —
instruments, strategy parameters, risk limits, file paths — lives here so the
strategies and risk manager stay free of magic numbers.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Alpaca credentials / environment -------------------------------------
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
# Paper trading by default. Set ALPACA_PAPER=false in .env to go live.
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").strip().lower() in ("1", "true", "yes")
# "iex" is available on the free data plan; "sip" requires a paid subscription.
STOCK_DATA_FEED = os.getenv("STOCK_DATA_FEED", "iex").strip().lower()

# --- Risk management --------------------------------------------------------
# A 1 ATR adverse move equals this fraction of account equity.
RISK_PER_TRADE = 0.01
ATR_PERIOD = 14
# Safety cap: a single position's notional value may not exceed this fraction
# of equity, so a very quiet instrument can't consume the whole account.
MAX_POSITION_NOTIONAL_PCT = 0.50

# Correlation filter: block new longs on `blocked_symbol` while every symbol
# in `if_all_long` already holds a long position.
CORRELATION_FILTER = {
    "blocked_symbol": "BTC/USD",
    "if_all_long": ["SPY", "QQQ"],
}

# --- Instruments & strategies ----------------------------------------------
STRATEGY_CONFIGS = [
    {
        "strategy": "mean_reversion",
        "symbol": "SPY",
        "asset_class": "us_equity",
        "timeframe_minutes": 15,
        "params": {"period": 20, "band": 1.5},
    },
    {
        "strategy": "mean_reversion",
        "symbol": "QQQ",
        "asset_class": "us_equity",
        "timeframe_minutes": 15,
        "params": {"period": 20, "band": 1.8},
    },
    {
        "strategy": "momentum_breakout",
        "symbol": "BTC/USD",
        "asset_class": "crypto",
        "timeframe_minutes": 60,
        # Alpaca crypto is long-only: a confirmed breakdown exits the long.
        "params": {"period": 20, "volume_mult": 1.5, "trail_atr_mult": 2.0,
                   "allow_short": False},
    },
    {
        "strategy": "trend_following",
        "symbol": "GLD",
        "asset_class": "us_equity",
        "timeframe_minutes": 240,
        "params": {"fast": 50, "slow": 200, "trail_atr_mult": 3.0,
                   "allow_short": True},
    },
    {
        "strategy": "trend_following",
        "symbol": "USO",
        "asset_class": "us_equity",
        "timeframe_minutes": 240,
        "params": {"fast": 50, "slow": 200, "trail_atr_mult": 3.0,
                   "allow_short": True},
    },
]

# --- Runtime ----------------------------------------------------------------
# How often the main loop wakes up to check stops and bar boundaries.
POLL_SECONDS = 60
# Seconds to wait for a market order to fill before giving up on it.
ORDER_FILL_TIMEOUT = 30

# --- Logging ----------------------------------------------------------------
LOG_DIR = Path(os.getenv("LOG_DIR", "."))
TRADES_CSV = LOG_DIR / "trades.csv"
DAILY_PNL_CSV = LOG_DIR / "daily_pnl.csv"
BOT_LOG = LOG_DIR / "bot.log"
