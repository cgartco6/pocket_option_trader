# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
import pytz
from config import *

class TradingSignalGenerator:
    def __init__(self):
        self.base_url = API_URL
        self.last_fetch_time = {}
        
    def fetch_data(self, symbol):
        """Retrieve market data from API"""
        # Construct symbol for Binance API
        binance_symbol = symbol.replace("/", "")
        if "/" in symbol:  # Crypto pairs
            binance_symbol += "T"
        
        params = {
            'symbol': binance_symbol,
            'interval': TIMEFRAME,
            'limit': MAX_CANDLES
        }
        
        try:
            # Add cache busting to avoid stale data
            cache_param = int(time.time() * 1000)
            response = requests.get(
                self.base_url, 
                params=params,
                headers={'Cache-Control': 'no-cache'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) < 30:
                print(f"Insufficient data for {symbol}")
                return None
                
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric types
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            
            # Convert timestamp
            df['date'] = pd.to_datetime(df['open_time'], unit='ms')
            
            # Clean and return
            return df.dropna().reset_index(drop=True)
            
        except requests.exceptions.RequestException as e:
            print(f"Network error ({symbol}): {str(e)}")
        except Exception as e:
            print(f"Processing error ({symbol}): {str(e)}")
        return None

    def calculate_rsi(self, df):
        """Calculate Relative Strength Index with smoothing"""
        delta = df['close'].diff(1)
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # Use Wilder's smoothing method
        avg_gain = gain.ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        return df

    def calculate_macd(self, df):
        """Calculate MACD indicator with histogram"""
        ema_fast = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
        ema_slow = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['signal'] = df['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        df['histogram'] = df['macd'] - df['signal']
        return df

    def generate_signal(self, df, pair):
        """Generate trading signal with strict conditions"""
        if df is None or len(df) < 30:
            return "NO DATA", None, None, None
        
        # Calculate indicators
        df = self.calculate_rsi(df)
        df = self.calculate_macd(df)
        
        # Use last 3 candles for confirmation
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        prev_prev_row = df.iloc[-3]
        
        # Strict signal conditions
        buy_conditions = [
            last_row['rsi'] < RSI_OVERSOLD,
            last_row['macd'] > last_row['signal'],
            prev_row['macd'] <= prev_row['signal'],
            prev_prev_row['macd'] < prev_prev_row['signal'],
            last_row['histogram'] > 0,
            last_row['close'] > last_row['open'],
            last_row['close'] > df['close'].iloc[-10:-1].mean()  # Above short-term MA
        ]
        
        sell_conditions = [
            last_row['rsi'] > RSI_OVERBOUGHT,
            last_row['macd'] < last_row['signal'],
            prev_row['macd'] >= prev_row['signal'],
            prev_prev_row['macd'] > prev_prev_row['signal'],
            last_row['histogram'] < 0,
            last_row['close'] < last_row['open'],
            last_row['close'] < df['close'].iloc[-10:-1].mean()  # Below short-term MA
        ]
        
        # Get signal time (UTC)
        signal_time = datetime.utcfromtimestamp(
            last_row['open_time']/1000
        ).replace(tzinfo=pytz.utc)
        
        # Determine signal type
        if all(buy_conditions):
            signal_type = "BUY"
        elif all(sell_conditions):
            signal_type = "SELL"
        else:
            return "HOLD", None, None, None
        
        # Signal confirmation and duration analysis
        direction, duration = self.analyze_trade_duration(df, signal_type)
        return signal_type, signal_time, direction, duration

    def analyze_trade_duration(self, df, signal_type):
        """Analyze trade duration and confirmation"""
        if len(df) < 3:
            return "N/A", "N/A"
        
        signal_idx = len(df) - 1
        signal_close = df.iloc[signal_idx]['close']
        
        # Check next candle
        next_idx = min(signal_idx + 1, len(df) - 1)
        next_candle = df.iloc[next_idx]
        next_close = next_candle['close']
        
        # Determine if next candle confirms signal
        direction_match = (
            (signal_type == "BUY" and next_close > signal_close) or 
            (signal_type == "SELL" and next_close < signal_close)
        )
        
        if not direction_match:
            return "REVERSED", "Immediate"
        
        # Calculate duration until reversal
        duration = 1
        for i in range(signal_idx + 2, min(signal_idx + 10, len(df))):
            current_close = df.iloc[i]['close']
            prev_close = df.iloc[i-1]['close']
            
            reversal_condition = (
                (signal_type == "BUY" and current_close < prev_close) or
                (signal_type == "SELL" and current_close > prev_close)
            )
            
            if reversal_condition:
                break
            duration += 1
        
        # Convert to time (5 min per candle)
        minutes = duration * 5
        return "CONFIRMED", f"{minutes} mins"

    def get_all_signals(self):
        """Generate signals for all trading pairs"""
        signals = {}
        for pair in TRADING_PAIRS:
            try:
                df = self.fetch_data(pair)
                signals[pair] = self.generate_signal(df, pair)
                time.sleep(0.15)  # Avoid rate limiting
            except Exception as e:
                print(f"Error processing {pair}: {str(e)}")
                signals[pair] = ("ERROR", None, None, None)
        return signals
