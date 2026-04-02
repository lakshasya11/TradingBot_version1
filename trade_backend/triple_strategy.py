import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

# --- Helper function for Triple Confirmation Indicators ---
def _calculate_triple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates RSI(14), EMA(9), EMA(21), Supertrend(5, 0.7), and ATR(10).
    """
    df = df.copy()
    
    # 1. RSI(14) - Manual calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 2. EMA(9) and EMA(21)
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    # 3. Simple Supertrend calculation
    hl2 = (df['high'] + df['low']) / 2
    atr = df['high'].rolling(5).max() - df['low'].rolling(5).min()
    upper_band = hl2 + (0.7 * atr)
    lower_band = hl2 - (0.7 * atr)
    
    # Simple trend direction based on close vs bands
    df['supertrend_direction'] = np.where(df['close'] > upper_band.shift(1), 1, 
                                         np.where(df['close'] < lower_band.shift(1), -1, 0))
    
    # 4. ATR(14) for stop loss
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr14'] = true_range.rolling(14).mean()
        
    return df

class TripleConfirmationBot:
    
    # Define the required timeframes and their MT5 values
    MULTI_TF_MAP = {
        '1M': mt5.TIMEFRAME_M1,
        '5M': mt5.TIMEFRAME_M5,
        '15M': mt5.TIMEFRAME_M15,
        '30M': mt5.TIMEFRAME_M30,
        '1H': mt5.TIMEFRAME_H1,
        '1D': mt5.TIMEFRAME_D1
    }
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.log_queue = []  # Simple list for logging
        self.multi_tf_data: Dict[str, pd.DataFrame] = {}  # Storage for 6 TFs
        self.is_running = False

    def log(self, message: str):
        """Simple logging utility."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{self.symbol}] {message}"
        print(log_entry)
        self.log_queue.append(log_entry)

    def fetch_multi_timeframe_data(self):
        """Fetches data for all 6 timeframes and calculates indicators."""
        self.log("Starting Multi-Timeframe Data Fetch...")
        for tf_name, tf_value in self.MULTI_TF_MAP.items():
            try:
                # Fetch last 500 bars for calculation stability
                rates = mt5.copy_rates_from_pos(self.symbol, tf_value, 0, 500) 
                
                if rates is not None and len(rates) > 30:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df = _calculate_triple_indicators(df)
                    self.multi_tf_data[tf_name] = df
                    self.log(f"✅ Data for {tf_name} loaded ({len(df)} bars).")
                else:
                    self.log(f"⚠️ Data for {tf_name} failed or insufficient data.")
                    
            except Exception as e:
                self.log(f"❌ Error fetching {tf_name} data: {e}")

    def check_multi_timeframe_consensus(self):
        """
        Checks for UNANIMOUS Triple Confirmation signal across all 6 timeframes.
        Entry is allowed ONLY if ALL 6 TFs agree on ALL 3 indicators.
        """
        timeframes = self.MULTI_TF_MAP.keys()
        
        consensus_buy = True
        consensus_sell = True
        
        for tf_name in timeframes:
            data_df = self.multi_tf_data.get(tf_name)
            
            # If any data is missing, we cannot establish consensus
            if data_df is None or data_df.empty or len(data_df) < 30: 
                self.log(f"❌ Consensus broken: Data missing/incomplete for {tf_name}.")
                return "NONE" 
                
            last = data_df.iloc[-1]
            
            # --- BUY Conditions (RSI > 50 AND ST Up AND EMA9 > EMA21) ---
            rsi_buy = last['rsi'] > 50
            st_buy = last['supertrend_direction'] == 1 
            ema_buy = last['ema9'] > last['ema21']
            
            # --- SELL Conditions (RSI < 40 AND ST Down AND EMA9 < EMA21) ---
            rsi_sell = last['rsi'] < 40
            st_sell = last['supertrend_direction'] == -1
            ema_sell = last['ema9'] < last['ema21']
            
            # Check if the current TF supports the overall BUY consensus
            if not (rsi_buy and st_buy and ema_buy):
                consensus_buy = False
                
            # Check if the current TF supports the overall SELL consensus
            if not (rsi_sell and st_sell and ema_sell):
                consensus_sell = False
                
            # Early Exit: If neither BUY nor SELL is possible, stop checking
            if not consensus_buy and not consensus_sell:
                return "NONE"
                
        # Final Decision
        if consensus_buy and not consensus_sell:
            return "UNIFIED_BUY_TRIPLE_CONFIRM"
            
        elif consensus_sell and not consensus_buy:
            return "UNIFIED_SELL_TRIPLE_CONFIRM"
            
        else:
            # Handles cases where both are false or contradictory
            return "NONE"

    def calculate_atr_stop_loss(self, direction, entry_price):
        """Calculate stop loss using ATR from 15M timeframe"""
        tf_15m = self.multi_tf_data.get('15M')
        if tf_15m is None or tf_15m.empty:
            # Fallback to fixed stop loss
            return entry_price * 0.98 if direction == "BUY" else entry_price * 1.02
        
        atr = tf_15m['atr14'].iloc[-1]
        atr_multiplier = 1.5  # 1.5x ATR for stop loss
        sl = entry_price - (atr * atr_multiplier) if direction == "BUY" else entry_price + (atr * atr_multiplier)
        
        self.log(f"📐 ATR SL | ATR(14): {atr:.5f} | Multiplier: {atr_multiplier} | SL: {sl:.5f}")
        return sl
    
    def execute_trade(self, signal):
        """Execute trade with ATR-based stop loss"""
        direction = "BUY" if "BUY" in signal else "SELL"
        
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                self.log("Failed to get tick data")
                return

            entry_price = tick.ask if direction == "BUY" else tick.bid
            stop_loss = self.calculate_atr_stop_loss(direction, entry_price)
            
            # Take profit at 2:1 risk reward
            risk = abs(entry_price - stop_loss)
            take_profit = entry_price + (risk * 2) if direction == "BUY" else entry_price - (risk * 2)
            
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                self.log("Failed to get symbol info")
                return
            
            # Round to symbol digits
            digits = symbol_info.digits
            stop_loss = round(stop_loss, digits)
            take_profit = round(take_profit, digits)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "magic": 123456,
                "comment": signal[:31],
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log(f"✅ ORDER EXECUTED: {signal} | SL: {stop_loss} | TP: {take_profit}")
            else:
                self.log(f"❌ ORDER FAILED: {result.comment if result else 'Unknown error'}")

        except Exception as e:
            self.log(f"❌ Error executing trade: {e}")

    def run_strategy_cycle(self):
        """Simple loop to run data fetch and signal check."""
        if not self.is_running:
            self.log("Strategy is not running.")
            return
            
        self.fetch_multi_timeframe_data()
        signal = self.check_multi_timeframe_consensus()
        
        if signal != "NONE":
            self.log(f"🎯 EXECUTE SIGNAL: {signal}")
            self.execute_trade(signal)
        else:
            self.log(f"Status: {signal}")