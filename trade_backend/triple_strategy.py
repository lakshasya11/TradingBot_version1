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
    
    # 2. EMA(9) and EMA(21) --- commented out (replaced by UT Bot)
    # df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    # df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()

    # 3. Simple Supertrend calculation --- commented out
    # hl2 = (df['high'] + df['low']) / 2
    # atr = df['high'].rolling(5).max() - df['low'].rolling(5).min()
    # upper_band = hl2 + (0.7 * atr)
    # lower_band = hl2 - (0.7 * atr)
    # df['supertrend_direction'] = np.where(df['close'] > upper_band.shift(1), 1,
    #                                      np.where(df['close'] < lower_band.shift(1), -1, 0))

    # --- UT Bot Trailing Stop (Key_Value=2.0, ATR_Period=1) ---
    close_arr = df['close'].values
    high_arr  = df['high'].values
    low_arr   = df['low'].values
    n = len(close_arr)
    atr_arr = np.abs(high_arr - low_arr)
    trail = np.zeros(n)
    trail[0] = close_arr[0]
    for i in range(1, n):
        n_loss = 2.0 * atr_arr[i]
        prev_stop  = trail[i - 1]
        prev_close = close_arr[i - 1]
        if close_arr[i] > prev_stop and prev_close > prev_stop:
            trail[i] = max(prev_stop, close_arr[i] - n_loss)
        elif close_arr[i] < prev_stop and prev_close < prev_stop:
            trail[i] = min(prev_stop, close_arr[i] + n_loss)
        elif close_arr[i] > prev_stop:
            trail[i] = close_arr[i] - n_loss
        else:
            trail[i] = close_arr[i] + n_loss
    df['ut_trail'] = trail
    df['ut_buy']  = (df['close'] > df['ut_trail']) & (df['close'].shift(1) <= df['ut_trail'].shift(1))
    df['ut_sell'] = (df['close'] < df['ut_trail']) & (df['close'].shift(1) >= df['ut_trail'].shift(1))

    df['ut_bullish'] = df['close'] > df['ut_trail']
    df['ut_bearish'] = df['close'] < df['ut_trail']

    # 4. ATR(20) for stop loss
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr14'] = true_range.rolling(20).mean()
        
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
        self.log_queue = []
        self.multi_tf_data: Dict[str, pd.DataFrame] = {}
        self.is_running = False
        self.breakeven_activated = {}   # ticket: True
        self.trailing_sl = {}           # ticket: current trailing sl value
        self.breakeven_points = 3.0
        self.trailing_points = 1.0
        self.trailing_gap = 1.0

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
                rates = mt5.copy_rates_from_pos(self.symbol, tf_value, 0, 100) 
                
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
        New Consensus for 5M Trading:
        1. Trigger: 5M chart must show a fresh UT crossover.
        2. Trend: 15M and 1H charts must be on the same side of the UT line.
        """
        # 1. Check 5M Trigger
        df_5m = self.multi_tf_data.get('5M')
        if df_5m is None or df_5m.empty:
            return "NONE"
        
        last_5m = df_5m.iloc[-1]
        candle_green_5m = last_5m['close'] > last_5m['open']
        candle_red_5m   = last_5m['close'] < last_5m['open']

        # BUY: ut_buy + RSI > 50 + GREEN candle (ALL 3 must be true)
        trigger_buy  = last_5m['ut_buy'] and last_5m['rsi'] > 50 and candle_green_5m
        # SELL: ut_sell + RSI < 50 + RED candle (ALL 3 must be true)
        trigger_sell = last_5m['ut_sell'] and last_5m['rsi'] < 50 and candle_red_5m

        if not trigger_buy and not trigger_sell:
            return "NONE"

        # 2. Check 15M Trend
        df_15m = self.multi_tf_data.get('15M')
        if df_15m is None or df_15m.empty:
            return "NONE"
        last_15m = df_15m.iloc[-1]
        
        # 3. Check 1H Trend
        df_1h = self.multi_tf_data.get('1H')
        if df_1h is None or df_1h.empty:
            return "NONE"
        last_1h = df_1h.iloc[-1]

        # Final Unified Signals
        if trigger_buy and last_15m['ut_bullish'] and last_1h['ut_bullish']:
            self.log("🎯 5M BUY TRIGGER with 15M/1H Trend Confirmation")
            return "UNIFIED_BUY_TRIPLE_CONFIRM"
            
        elif trigger_sell and last_15m['ut_bearish'] and last_1h['ut_bearish']:
            self.log("🎯 5M SELL TRIGGER with 15M/1H Trend Confirmation")
            return "UNIFIED_SELL_TRIPLE_CONFIRM"
            
        return "NONE"

    def calculate_stop_loss(self, direction, entry_price):
        """Calculate stop loss using tighter of ATR SL or UT Trail from 15M timeframe"""
        tf_15m = self.multi_tf_data.get('15M')
        if tf_15m is None or tf_15m.empty:
            return entry_price * 0.98 if direction == "BUY" else entry_price * 1.02

        atr = tf_15m['atr14'].iloc[-1]
        ut_sl = tf_15m['ut_trail'].iloc[-1]
        atr_multiplier = 1.5

        if direction == "BUY":
            atr_sl = entry_price - (atr * atr_multiplier)
            stop_loss = max(atr_sl, ut_sl)  # closer to entry = higher
        else:
            atr_sl = entry_price + (atr * atr_multiplier)
            stop_loss = min(atr_sl, ut_sl)  # closer to entry = lower

        sl_source = "UT Trail" if (direction == "BUY" and ut_sl > atr_sl) or (direction == "SELL" and ut_sl < atr_sl) else "ATR SL"
        self.log(f"📐 SL Source: {sl_source} | ATR SL: {atr_sl:.5f} | UT Trail: {ut_sl:.5f} | Final SL: {stop_loss:.5f}")
        return stop_loss, ut_sl
    
    def execute_trade(self, signal):
        """Execute trade with ATR-based stop loss"""
        direction = "BUY" if "BUY" in signal else "SELL"
        
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                self.log("Failed to get tick data")
                return

            entry_price = tick.ask if direction == "BUY" else tick.bid
            stop_loss, ut_trail_at_entry = self.calculate_stop_loss(direction, entry_price)
            
            # Take profit at 10.0 points distance
            tp_distance = 10.0
            take_profit = entry_price + tp_distance if direction == "BUY" else entry_price - tp_distance
            
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
                # Store bid_at_entry for accurate price_move (avoids spread distortion)
                # BUY: store tick.bid | SELL: store tick.ask
                if not hasattr(self, '_bid_at_entry'):
                    self._bid_at_entry = {}
                self._bid_at_entry[result.order] = tick.bid if direction == 'BUY' else tick.ask
                self._entry_time = getattr(self, '_entry_time', {})
                self._entry_time[result.order] = datetime.now()
                self._ut_trail_at_entry = {result.order: {'direction': direction, 'ut_trail': ut_trail_at_entry}}
            else:
                self.log(f"❌ ORDER FAILED: {result.comment if result else 'Unknown error'}")

        except Exception as e:
            self.log(f"❌ Error executing trade: {e}")

    def check_exit_conditions(self):
        """Breakeven, trailing stop, and UT Trail exit"""
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            self._ut_trail_at_entry = getattr(self, '_ut_trail_at_entry', {})
            return
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            return
        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info:
            return

        for pos in positions:
            ticket = pos.ticket
            current_sl = pos.sl
            current_tp = pos.tp
            digits = symbol_info.digits
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"

            # Fix 1: restart-safe bid_at_entry fallback with spread estimate
            spread = tick.ask - tick.bid
            if not hasattr(self, '_bid_at_entry'):
                self._bid_at_entry = {}
            if ticket not in self._bid_at_entry:
                self._bid_at_entry[ticket] = pos.price_open - spread if direction == 'BUY' else pos.price_open + spread
            bid_at_entry = self._bid_at_entry[ticket]
            price_move = (tick.bid - bid_at_entry) if direction == "BUY" else (bid_at_entry - tick.ask)

            tf_15m = self.multi_tf_data.get('15M')
            live_trail = tf_15m['ut_trail'].iloc[-1] if tf_15m is not None and not tf_15m.empty else 0
            atr = tf_15m['atr14'].iloc[-1] if tf_15m is not None and not tf_15m.empty else 0
            sl_distance = atr * 1.5

            # Fix 2: ATR SL safety net FIRST — exit immediately, skip trailing/UT trail
            if sl_distance > 0:
                if direction == "BUY":
                    atr_sl = pos.price_open - sl_distance
                    if tick.bid <= atr_sl:
                        self.log(f"🔴 ATR SL Hit BUY #{ticket} | Bid: {tick.bid:.5f} <= ATR SL: {atr_sl:.5f}")
                        self._close_position(pos)
                        self.trailing_sl.pop(ticket, None)
                        continue
                else:
                    atr_sl = pos.price_open + sl_distance
                    if tick.ask >= atr_sl:
                        self.log(f"🟢 ATR SL Hit SELL #{ticket} | Ask: {tick.ask:.5f} >= ATR SL: {atr_sl:.5f}")
                        self._close_position(pos)
                        self.trailing_sl.pop(ticket, None)
                        continue

            # Fix 3: UT Trail Exit — 10s grace period after entry
            self._entry_time = getattr(self, '_entry_time', {})
            entry_time = self._entry_time.get(ticket, None)
            hold_seconds = (datetime.now() - entry_time).total_seconds() if entry_time else 999
            if live_trail and hold_seconds >= 10:
                if direction == "BUY" and tick.bid < live_trail:
                    self.log(f"🔴 UT Trail Exit BUY #{ticket} | Bid: {tick.bid:.5f} < Live Trail: {live_trail:.5f}")
                    self._close_position(pos)
                    self.breakeven_activated.pop(ticket, None)
                    self.trailing_sl.pop(ticket, None)
                    continue
                elif direction == "SELL" and tick.ask > live_trail:
                    self.log(f"🟢 UT Trail Exit SELL #{ticket} | Ask: {tick.ask:.5f} > Live Trail: {live_trail:.5f}")
                    self._close_position(pos)
                    self.breakeven_activated.pop(ticket, None)
                    self.trailing_sl.pop(ticket, None)
                    continue

            # UT Trail SL Sync - Update broker SL to live UT trail (red dotted line)
            if live_trail and live_trail > 0 and hold_seconds >= 10:
                ut_sl_rounded = round(live_trail, digits)
                # Only update if UT trail is better (tighter) than current SL
                should_update = False
                if direction == "BUY":
                    should_update = ut_sl_rounded > current_sl
                else:
                    should_update = current_sl == 0 or ut_sl_rounded < current_sl
                
                if should_update and abs(ut_sl_rounded - current_sl) >= symbol_info.point:
                    self.log(f"📍 UT Trail SL Sync #{ticket} | Trail: {ut_sl_rounded:.5f}")
                    self._modify_sl(ticket, ut_sl_rounded, current_tp)
                    current_sl = ut_sl_rounded

            # Fix 4: Trailing stop with zero guard for SELL current_sl
            if price_move >= self.trailing_points:
                if direction == "BUY":
                    new_sl = round(tick.bid - self.trailing_gap, digits)
                    if new_sl > current_sl:
                        self._modify_sl(ticket, new_sl, current_tp)
                        self.trailing_sl[ticket] = new_sl
                        self.log(f"🚀 Trailing SL BUY #{ticket} → {new_sl:.5f}")
                else:
                    new_sl = round(tick.ask + self.trailing_gap, digits)
                    if current_sl == 0 or new_sl < current_sl:
                        self._modify_sl(ticket, new_sl, current_tp)
                        self.trailing_sl[ticket] = new_sl
                        self.log(f"🚀 Trailing SL SELL #{ticket} → {new_sl:.5f}")

    def _modify_sl(self, ticket: int, new_sl: float, new_tp: float):
        """Modify position SL/TP"""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl": new_sl,
            "tp": new_tp
        }
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.log(f"✅ SL modified #{ticket} → {new_sl:.5f}")

    def _close_position(self, pos):
        """Close a position at market price"""
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            return
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": price,
            "magic": 123456,
            "comment": "UT Trail Exit",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            self.log(f"🏁 Position #{pos.ticket} closed. Reason: UT Trail Exit")
            self._ut_trail_at_entry.pop(pos.ticket, None)

    def run_strategy_cycle(self):
        """Simple loop to run data fetch and signal check."""
        if not self.is_running:
            self.log("Strategy is not running.")
            return
            
        self.fetch_multi_timeframe_data()
        signal = self.check_multi_timeframe_consensus()

        if signal != "NONE" and not mt5.positions_get(symbol=self.symbol):
            self.log(f"🎯 EXECUTE SIGNAL: {signal}")
            self.execute_trade(signal)
        else:
            self.log(f"Status: {signal}")

        # Monitor all exit conditions every cycle
        self.check_exit_conditions()