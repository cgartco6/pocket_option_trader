# -*- coding: utf-8 -*-
# Configuration Settings

# Trading assets with 92%+ payouts
TRADING_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD",
    "AUD/USD", "USD/CAD", "NZD/USD", "BCH/USD"
]

# API Configuration
API_URL = "https://api.binance.com/api/v3/klines"
TIMEFRAME = "5m"  # 5-minute candles

# Technical Indicator Parameters
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Trading Strategy Parameters
RSI_OVERBOUGHT = 68  # Default: 68
RSI_OVERSOLD = 32    # Default: 32
CONFIRMATION_CANDLES = 2  # Number of candles for confirmation

# Application Settings
REFRESH_INTERVAL = 30  # Seconds between updates
UI_THEME = "system"   # Options: light/dark/system
SOUND_ALERTS = True   # Play sound for new signals
MAX_CANDLES = 100     # Number of candles to fetch

# Pocket Option Credentials (Placeholder)
PO_EMAIL = "your@email.com"
PO_PASSWORD = "yourpassword"
