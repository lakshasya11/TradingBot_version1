import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import math
from datetime import datetime
from typing import Dict, Any, Optional
from terminal_formatter import TerminalFormatter
from trading_core import TradingCore
from indicators import TechnicalIndicators
from mt5_connection import MT5Connection
from tick_config import REQUIRED_CONFIRMATIONS, CONFIRMATION_WINDOW
from ema7_config import (
    # EMA7_ANGLE_BUY_THRESHOLD, EMA7_ANGLE_SELL_THRESHOLD,
    RSI_BUY_THRESHOLD, RSI_SELL_THRESHOLD,
    FIXED_SL_POINTS, TP_POINTS, TRAILING_POINTS, TRAILING_GAP
)
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("Matplotlib not available. Chart display disabled.")

class EnhancedTradingStrategy:
    
    TIMEFRAMES = {
        'M1': mt5.TIMEFRAME_M1,
        'M5': mt5.TIMEFRAME_M5,
        'M15': mt5.TIMEFRAME_M15,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H4': mt5.TIMEFRAME_H4,
        'D1': mt5.TIMEFRAME_D1
    }
    
    def __init__(self, symbol: str, base_timeframe: str = 'M1', enable_chart: bool = False):
        self.symbol = symbol
        self.base_timeframe = base_timeframe
        self.data_cache = {}
        self.open_positions = {}
        self.tick_count = 0
        self.enable_chart = False  # DISABLE chart in strategy - let bot handle it
        self.formatter = TerminalFormatter()
        self.trades_today = 0
        self.session_capital = 7149.74  # Starting capital
        
        # Single tick entry - no history or momentum tracking needed
        # All parameters removed for immediate execution
        
        # Track previous profitable exits for "above profit" entry condition
        self.last_profitable_exit_price = None
        self.last_profitable_direction = None
        
        # Exit Configuration (Loaded from ema7_config.py)
        self.atr_sl_multiplier = 1.5    # Stop loss at 1.5x ATR
        self.tp_points = TP_POINTS      # Take profit points
        self.trailing_points = TRAILING_POINTS  # Profit points to activate trail
        self.trailing_gap = TRAILING_GAP        # Points trail behind price
        self.fixed_sl_points = FIXED_SL_POINTS  # Fixed stop loss points
        self.opposite_candle_exit_points = 0.5  # Exit on opposite candle + 0.5 point reversal
        
        # Single tick entry - no confirmation system needed
        self.required_confirmations = 0
        self.confirmation_window = 0

    # Using shared modules - duplicate functions removed




        
    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")

    def fetch_data(self, timeframe: str, bars: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data with minimal delay"""
        tf_const = self.TIMEFRAMES[timeframe]
            
        # Fetch fresh data every tick (no cache)
        rates = mt5.copy_rates_from_pos(self.symbol, tf_const, 0, bars)

        
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
        
        return pd.DataFrame()


















    def analyze_timeframe(self, timeframe: str) -> Dict:
        """EMA 7 based analysis"""
        df = self.fetch_data(timeframe, bars=100)
        if df.empty or len(df) < 50:
            return {}
        
        close = df['close']
        
        # Use shared indicators for calculations
        rsi = TechnicalIndicators.calculate_rsi(close, 14)
        atr_val = TechnicalIndicators.calculate_atr(df, period=20)
        # EMA 7 Calculations Commented Out
        # ema7 = TechnicalIndicators.calculate_ema7(close)
        
        # Cache ATR for calculations
        self._current_atr = atr_val.iloc[-1] if len(atr_val) > 0 and not pd.isna(atr_val.iloc[-1]) else 0.01
        
        # Calculate EMA 7 angle - Commented Out
        # try:
        #     ema7_angle = TechnicalIndicators.calculate_ema7_angle(ema7, self.symbol)
        # except Exception as e:
        #     self.log(f"[ERROR] Error in EMA7 angle calculation: {e}")
        ema7_angle = 0.0
        
        # EMA 7 signals - Commented Out
        close_current = close.iloc[-1]
        # ema7_current = ema7.iloc[-1]
        # ema7_buy = bool(close_current > ema7_current)
        # ema7_sell = bool(close_current < ema7_current)
        ema7_current = 0.0
        ema7_buy = False
        ema7_sell = False
        
        # Candle color detection (with fallback for first-run data)
        completed_close = close.iloc[-1]
        completed_open = df['open'].iloc[-1]
        candle_color = 'GREEN' if completed_close > completed_open else 'RED'
        current_candle_color = candle_color
        
        if len(df) >= 2:
            completed_close = df['close'].iloc[-2]
            completed_open = df['open'].iloc[-2]
            candle_color = 'GREEN' if completed_close > completed_open else 'RED'
            
            current_close = df['close'].iloc[-1]
            current_open = df['open'].iloc[-1]
            current_candle_color = 'GREEN' if current_close > current_open else 'RED'
        
        # Get positions and tick for trail calculation
        positions = mt5.positions_get(symbol=self.symbol)
        tick = mt5.symbol_info_tick(self.symbol)
        # ut_trail = self.calculate_dynamic_ema7_trail(df, positions, tick)

        return {
                'rsi': rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50,
                'atr': atr_val.iloc[-1] if len(atr_val) > 0 and not pd.isna(atr_val.iloc[-1]) else 0.01,
                'close': close.iloc[-1],
                'open': df['open'].iloc[-1],
                'low': df['low'].iloc[-1],
                'high': df['high'].iloc[-1],
                'candle_color': current_candle_color,
                'completed_candle_color': candle_color,
                'prev_close': completed_close if len(df) >= 2 else close.iloc[-1],
                'prev_open': completed_open if len(df) >= 2 else df['open'].iloc[-1],
                # 'ema7_buy': ema7_buy,
                # 'ema7_sell': ema7_sell,
                # 'ema7_angle': ema7_angle,
                # 'trail_stop': ema7_current,
                # 'ut_trail_array': ut_trail,
                'candle_time': df.index[-1],
                'df': df
            }




    # def calculate_dynamic_ema7_trail(self, df: pd.DataFrame, positions, tick) -> np.ndarray:
    #     """Simple EMA 7 calculation for chart display"""
    #     ema7 = TechnicalIndicators.calculate_ema7(df['close'])
    #     return ema7.values



    # Removed - not needed for single tick entry





    def check_entry_conditions(self, analysis: Dict) -> str:
        """Dual-Mode Entry Logic: Trend-Following Breakouts + Counter-Trend Reversals"""
        if not analysis:
            return "NONE"

        rsi = analysis.get('rsi', 50)
        ema7_buy = analysis.get('ema7_buy', False)  # Price > EMA7
        ema7_sell = analysis.get('ema7_sell', False) # Price < EMA7
        ema7_angle = analysis.get('ema7_angle', 0.0)
        prev_candle_color = analysis.get('completed_candle_color', '')
        prev_close = analysis.get('prev_close', 0) 
        prev_open = analysis.get('prev_open', 0)        
        current_price = analysis.get('close', 0)
        current_open = analysis.get('open', 0)
        current_color = "GREEN" if current_price > current_open else "RED"
        
        # --- EMA 7 Angle Requirement Commented Out ---
        # if ema7_angle > EMA7_ANGLE_BUY_THRESHOLD:
            # A. Trend-Following BUY (Breakout)
        if current_color == "GREEN" and rsi > RSI_BUY_THRESHOLD and current_price > prev_close:
            if prev_candle_color == "RED" and current_price <= prev_open:
                print(f"⏳ [ENTRY BLOCK] BUY Trend OK but waiting for Body Coverage: Price {current_price:.2f} <= PrevOpen {prev_open:.2f}")
                return "NONE"
            print(f"✅ [ENTRY OK] BUY BREAKOUT: Price {current_price:.2f} > PrevOpen {prev_open:.2f} (Body Covered!)")
            return "BUY"
        
        # B. Counter-Trend SELL (Reversal Bypass)
        if current_color == "RED" and prev_candle_color == "RED" and rsi > 30 and current_price < prev_close:
            print(f"💥 [REVERSAL SELL] RED after RED | RSI={rsi:.1f}")
            return "SELL"

        # elif ema7_angle < EMA7_ANGLE_SELL_THRESHOLD:
            # A. Trend-Following SELL (Breakdown)
        if current_color == "RED" and rsi < RSI_SELL_THRESHOLD and current_price < prev_close:
            if prev_candle_color == "GREEN" and current_price >= prev_open:
                print(f"⏳ [ENTRY BLOCK] SELL Trend OK but waiting for Body Coverage: Price {current_price:.2f} >= PrevOpen {prev_open:.2f}")
                return "NONE"
            print(f"✅ [ENTRY OK] SELL BREAKDOWN: Price {current_price:.2f} < PrevOpen {prev_open:.2f} (Body Covered!)")
            return "SELL"
        
        # B. Counter-Trend BUY (Reversal Bypass)
        if current_color == "GREEN" and prev_candle_color == "GREEN" and rsi < 70 and current_price > prev_close:
            print(f"💥 [REVERSAL BUY] GREEN after GREEN | RSI={rsi:.1f}")
            return "BUY"

        return "NONE"
        return "NONE"






    def execute_trade(self, signal: str, analysis: Dict):
        """Execute trade with fixed 1-point stop loss"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            if not tick or not symbol_info:
                self.log("Failed to get tick/symbol data")
                return

            entry_price = tick.ask if signal == "BUY" else tick.bid
            volume = TradingCore.calculate_dynamic_volume(entry_price, self.symbol)
            
            if volume <= 0:
                self.log("⚠️ Trade skipped - volume too small")
                return

            # Fixed 1-point stop loss
            if signal == "BUY":
                initial_sl = round(entry_price - self.fixed_sl_points, symbol_info.digits)
                take_profit = round(entry_price + self.tp_points, symbol_info.digits)
                order_type = mt5.ORDER_TYPE_BUY
            else:
                initial_sl = round(entry_price + self.fixed_sl_points, symbol_info.digits)
                take_profit = round(entry_price - self.tp_points, symbol_info.digits)
                order_type = mt5.ORDER_TYPE_SELL

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": entry_price,
                "sl": initial_sl,
                "tp": take_profit,
                "magic": 123456,
                "comment": f"{signal}_Fixed1ptSL",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.trades_today += 1
                conditions = f"RSI/{analysis.get('rsi', 0):.1f} Candle/{analysis.get('candle_color', '')}"
                
                self.formatter.print_trade_entry(
                    signal, entry_price, volume, initial_sl, take_profit, 
                    result.order, conditions, self.session_capital, self.trades_today
                )
                
                # Store position data
                current_candle_color, current_candle_time = TradingCore.get_candle_data(self.symbol, "M1")
                if not current_candle_color or not current_candle_time:
                    current_candle_color = analysis.get('candle_color', 'UNKNOWN')
                    current_candle_time = datetime.now()
                
                self.open_positions[result.order] = {
                    'entry_price': entry_price,
                    'reference_price': tick.bid if signal == 'BUY' else tick.ask,
                    'entry_time': datetime.now(),
                    'direction': signal,
                    'dollar_trail_active': False,
                    'dollar_trail_sl': None,
                    'phase': 'Fixed 1pt SL',
                    'entry_candle_color': current_candle_color,
                    'entry_candle_time': current_candle_time
                }
                
                self.log(f"✅ PHASE 1: Fixed 1pt SL Active | PHASE 2: Dynamic Trail after 0.01pts profit")
            else:
                self.log(f"❌ ORDER FAILED: {result.comment if result else 'Unknown error'}")
        except Exception as e:
            self.log(f"❌ Error executing trade: {e}")



    def check_exit_conditions(self, analysis: Dict):
        """Two-phase exit: Fixed 1pt SL + Dynamic trailing after 0.01pts profit"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if not positions:
                return

            tick = mt5.symbol_info_tick(self.symbol)
            symbol_info = mt5.symbol_info(self.symbol)
            if not tick or not symbol_info:
                return

            for pos in positions:
                ticket = pos.ticket
                pos_data = self.open_positions.setdefault(ticket, {})
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"

                # Phase 1: Fixed 1-point stop loss
                def profit_callback(profit_points, exit_price):
                    if profit_points > 0:
                        self.last_profitable_exit_price = exit_price
                        self.last_profitable_direction = direction
                
                if TradingCore.check_fixed_sl_exit(pos, tick, self.fixed_sl_points, profit_callback):
                    if pos.ticket in self.open_positions:
                        del self.open_positions[pos.ticket]
                    continue

                # Phase 1.5: Opposite candle + 0.5pt reversal exit
                if TradingCore.check_opposite_candle_exit(pos, tick, pos_data, self.symbol, self.opposite_candle_exit_points, "M1"):
                    if pos.ticket in self.open_positions:
                        del self.open_positions[pos.ticket]
                    continue

                # Phase 2: Dynamic trailing after 0.01pts profit
                try:
                    dollar_trail_sl, trail_active, phase_label = TradingCore.calculate_trailing_stop_points(
                        pos, tick, pos_data, symbol_info, self.trailing_points, self.trailing_gap
                    )
                except Exception as e:
                    self.log(f"❌ Error in calculate_trailing_stop_points: {e}")
                    continue

                # Apply dynamic trailing if active
                if trail_active and dollar_trail_sl is not None:
                    if direction == "BUY":
                        current_sl = pos.sl if pos.sl is not None else 0.0
                        if dollar_trail_sl > current_sl:
                            TradingCore.modify_position(ticket, self.symbol, dollar_trail_sl, pos.tp)
                    else:
                        current_sl = pos.sl if pos.sl is not None else float('inf')
                        if dollar_trail_sl < current_sl:
                            TradingCore.modify_position(ticket, self.symbol, dollar_trail_sl, pos.tp)
                
                # Show status occasionally
                if self.tick_count % 10 == 0:
                    reference_price = pos_data.get('reference_price', pos.price_open)
                    if direction == "BUY":
                        profit_points = tick.bid - reference_price if reference_price else 0.0
                        fixed_sl = round(pos.price_open - 1.0, 2)
                    else:
                        profit_points = reference_price - tick.ask if reference_price else 0.0
                        fixed_sl = round(pos.price_open + 1.0, 2)
                    
                    if trail_active:
                        self.log(f"📊 [{phase_label}] {direction} #{ticket} | SL: {dollar_trail_sl:.2f} | Profit: {profit_points:.3f}pts")
                    else:
                        self.log(f"📍 [Fixed 1pt SL] {direction} #{ticket} | SL: {fixed_sl:.2f} | Profit: {profit_points:.3f}pts | Need: 0.01pts for Dynamic Trail")
        except Exception as e:
            self.log(f"❌ Error in check_exit_conditions: {e}")
        




    def update_chart(self, analysis: Dict):
        """Update live chart with EMA 7"""
        if not self.enable_chart:
            return
            
        try:
            df = analysis.get('df')
            current_price = analysis.get('close')
            
            if df is None or len(df) < 10:
                return
                
            self.ax.clear()
            plot_df = df.tail(50).copy()
            ema7_plot = TechnicalIndicators.calculate_ema7(plot_df['close'])
            
            positions = mt5.positions_get(symbol=self.symbol)
            tick = mt5.symbol_info_tick(self.symbol)
            
            trail_array = ema7_plot.values.copy()
            
            # Show active exit level
            if positions and tick:
                pos = positions[0]
                pos_data = self.open_positions.get(pos.ticket, {})
                
                if pos_data.get('dollar_trail_active', False):
                    if pos.type == mt5.POSITION_TYPE_BUY:
                        trail_array[-1] = tick.bid - self.trailing_gap
                    else:
                        trail_array[-1] = tick.ask + self.trailing_gap
                else:
                    if pos.type == mt5.POSITION_TYPE_BUY:
                        trail_array[-1] = pos.price_open - self.fixed_sl_points
                    else:
                        trail_array[-1] = pos.price_open + self.fixed_sl_points
            
            x_range = range(len(plot_df))
            self.ax.plot(x_range, plot_df['close'], 'b-', linewidth=1.5, label='Price')
            self.ax.plot(x_range, trail_array, 'r:', linewidth=2, label='EMA 7 / Exit Level', alpha=0.8)
            
            self.ax.axhline(y=current_price, color='blue', linestyle='-', alpha=0.7, 
                          label=f'Current Price: {current_price:.2f}')
            
            if positions:
                pos = positions[0]
                color = 'green' if pos.type == mt5.POSITION_TYPE_BUY else 'red'
                self.ax.axhline(y=pos.price_open, color=color, linestyle='-', alpha=0.5,
                              label=f'Entry: {pos.price_open:.2f}')
                
                exit_level = trail_array[-1]
                self.ax.axhline(y=exit_level, color='red', linestyle='--', linewidth=1, alpha=0.7,
                              label=f'Exit Level: {exit_level:.2f}')
            
            self.ax.set_title(f'{self.symbol} - EMA 7 Strategy')
            self.ax.legend(loc='upper left')
            self.ax.grid(True, alpha=0.3)
            
            plt.draw()
            plt.pause(0.01)
            
        except Exception as e:
            print(f"[CHART ERROR] {e}")



    def run_strategy(self):
        """Main strategy execution loop"""
        self.tick_count += 1
        
        analysis = self.analyze_timeframe(self.base_timeframe)
        if not analysis:
            return
        
        signal = self.check_entry_conditions(analysis)
        positions = mt5.positions_get(symbol=self.symbol)
        
        # Determine status
        if positions:
            status = "IN_TRADE"
        elif signal == "SIDEWAYS":
            status = "SIDEWAYS"
        elif signal != "NONE":
            status = f"SIGNAL: {signal}"
        else:
            status = "WAITING"

        # Show signal detection
        if signal != "NONE":
            colored_rsi = self.formatter.colorize_rsi(f"RSI:{analysis.get('rsi', 0):.1f}")
            colored_trail = self.formatter.colorize_trail(f"Trail:{analysis.get('trail_stop', 0):.2f}")
            colored_candle = self.formatter.colorize_candle(f"Candle:{analysis.get('candle_color', '')}")
            colored_price = self.formatter.colorize_price(f"{analysis.get('close', 0):.2f}")
            
            signal_line = f"[SIGNAL] {signal} | {colored_rsi} | {colored_trail} | {colored_candle} | Low:{analysis.get('low', 0):.2f} | High:{analysis.get('high', 0):.2f}"
            print(signal_line)
        
        trade_info_str = ""
        if positions:
            pos0 = positions[0]
            tick0 = mt5.symbol_info_tick(self.symbol)
            if tick0:
                pos0_data = self.open_positions.get(pos0.ticket, {})
                
                if pos0.type == mt5.POSITION_TYPE_BUY:
                    reference_price = pos0_data.get('reference_price', pos0.price_open)
                    pm = tick0.bid - reference_price
                    trail_sl_live = round(tick0.bid - self.trailing_gap, 2)
                    pnl = (tick0.bid - pos0.price_open) * pos0.volume
                else:
                    reference_price = pos0_data.get('reference_price', pos0.price_open)
                    pm = reference_price - tick0.ask
                    trail_sl_live = round(tick0.ask + self.trailing_gap, 2)
                    pnl = (pos0.price_open - tick0.ask) * pos0.volume
                    
                trail_status = "ACTIVE" if pm >= self.trailing_points else f"need {self.trailing_points - pm:.2f}more"
                broker_sl = pos0.sl if pos0.sl is not None else 0.0
                trade_info_str = f"Move: {pm:.2f}pts | Trail: {trail_status} | TrailSL: {trail_sl_live:.2f} | BrokerSL: {broker_sl:.2f} | "
                
                self.formatter.print_position_update(
                    pos0.ticket, analysis['trail_stop'], analysis['close'],
                    analysis['rsi'], analysis['candle_color'], "IN_POSITION", pnl
                )
                return

        # Regular log output
        colored_price = self.formatter.colorize_price(f"{analysis['close']:.2f}")
        colored_trail = self.formatter.colorize_trail(f"{analysis['trail_stop']:.2f}")
        colored_rsi = self.formatter.colorize_rsi(f"{analysis['rsi']:.1f}")
        colored_candle = self.formatter.colorize_candle(analysis['candle_color'])
        colored_status = self.formatter.colorize_status(status)
        colored_tick = self.formatter.colorize_ticket(f"#{self.tick_count}")
        
        log_line = (
            f"Tick{colored_tick} | "
            f"Price: {colored_price} | "
            f"EMA7: {colored_trail} | "
            f"EMA7_Angle: {analysis.get('ema7_angle', 0):.1f}° | "
            f"RSI: {colored_rsi} | "
            f"Candle: {colored_candle} | "
            f"EMA7_Buy: {analysis['ema7_buy']} | EMA7_Sell: {analysis['ema7_sell']} | "
            + trade_info_str
            + f"Status: {colored_status}"
        )
        
        self.log(log_line)

        # Execute signals
        if signal != "NONE" and signal != "SIDEWAYS" and not positions:
            self.log(f"✅ {signal} IMMEDIATE ENTRY - Single tick execution!")
            self.execute_trade(signal, analysis)
        
        # Check exit conditions
        if positions:
            try:
                self.check_exit_conditions(analysis)
            except Exception as e:
                self.log(f"❌ Error in check_exit_conditions: {e}")

# Usage example
if __name__ == "__main__":
    import time
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        exit()
    
    # Create strategy instance with chart enabled
    strategy = EnhancedTradingStrategy("XAUUSD", "M1", enable_chart=True)
    
    # Run strategy loop
    try:
        while True:
            strategy.run_strategy()
            time.sleep(1)  # Check every 1 second for real-time
    except KeyboardInterrupt:
        print("\nStrategy stopped by user")
    finally:
        mt5.shutdown()