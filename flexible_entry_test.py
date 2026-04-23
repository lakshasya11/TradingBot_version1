import MetaTrader5 as mt5
import numpy as np
import time
from datetime import datetime
import pytz
import os
import sys
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy
from terminal_formatter import TerminalFormatter
from trading_core import TradingCore
from indicators import TechnicalIndicators
from mt5_connection import MT5Connection
from tick_config import REQUIRED_CONFIRMATIONS, CONFIRMATION_WINDOW
from ema7_config import (
    SIDEWAYS_THRESHOLD, SIDEWAYS_LOOKBACK, 
    FIXED_SL_POINTS, TP_POINTS, TRAILING_POINTS, TRAILING_GAP,
    REVERSAL_EXIT_POINTS
)
from mt5_chart_lines import MT5ChartLines  # Import MT5 chart drawing

# Enable Windows ANSI colors
def enable_windows_colors():
    """Enable ANSI colors on Windows"""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return True

# Enable colors at import
enable_windows_colors()

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    CHART_AVAILABLE = True
except ImportError:
    CHART_AVAILABLE = False
    print("Matplotlib not available. Chart display disabled.")

# ANSI color codes for terminal highlighting
class Colors:
    # Force enable colors by setting environment variable
    import os
    os.environ['FORCE_COLOR'] = '1'
    
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    PURPLE = '\033[95m'  # Same as MAGENTA
    ORANGE = '\033[38;5;208m'  # Orange color
    BLUE = '\033[94m'  # Blue color
    
    @staticmethod
    def get_candle_color(candle_type):
        """Get color based on candle type"""
        return Colors.GREEN if candle_type == 'GREEN' else Colors.RED
    
    @staticmethod
    def test_colors():
        """Test if colors are working"""
        print(f"{Colors.RED}RED{Colors.RESET} {Colors.GREEN}GREEN{Colors.RESET} {Colors.YELLOW}YELLOW{Colors.RESET} {Colors.BLUE}BLUE{Colors.RESET}")
        print(f"{Colors.MAGENTA}MAGENTA{Colors.RESET} {Colors.CYAN}CYAN{Colors.RESET} {Colors.ORANGE}ORANGE{Colors.RESET}")

class TradingBot:
    def __init__(self, symbol="XAUUSD", timeframe="M1", enable_chart=True):
        self.symbol = symbol
        self.timeframe = timeframe
        self.strategy = EnhancedTradingStrategy(symbol, timeframe)
        self.tick_count = 0
        self.session_start = time.time()
        self.enable_chart = enable_chart and CHART_AVAILABLE
        self.formatter = TerminalFormatter()
        
        # Chart setup - FORCE ENABLE WITH DEBUGGING
        if self.enable_chart:
            print("[CHART] Initializing matplotlib chart...")
            try:
                plt.ion()  # Interactive mode
                self.fig, self.ax = plt.subplots(figsize=(14, 10))  # Larger window
                plt.style.use('default')  # Ensure default style
                self.fig.suptitle(f'{self.symbol} - STOP LOSS & TAKE PROFIT LEVELS', fontsize=16, fontweight='bold')
                plt.show(block=False)  # Non-blocking show
                self.fig.canvas.draw()
                self.fig.canvas.flush_events()
                print("[CHART] ✅ Chart window created successfully")
                print("[CHART] 🔴 RED DASHED LINES = Stop Loss")
                print("[CHART] 🟢 GREEN DASHED LINES = Take Profit")
                print("[CHART] 🔵 RED DOTTED LINE = Active Exit Level")
            except Exception as e:
                print(f"[CHART] ❌ Failed to create chart: {e}")
                self.enable_chart = False
                self.fig = None
                self.ax = None
        else:
            print("[CHART] Chart disabled")
            self.fig = None
            self.ax = None
        
        # Trading state
        self.position_data = {}  # Store position-specific data
        self.last_candle_time = None
        self.fixed_sl_points = FIXED_SL_POINTS      # Use config value
        self.tp_points = TP_POINTS                  # Use config value
        self.trailing_points = TRAILING_POINTS      # Use config value
        self.trailing_gap = TRAILING_GAP            # Use config value
        self.reversal_exit_points = REVERSAL_EXIT_POINTS # Use config value
        
        # Get symbol info for contract size (P/L calculation)
        self.symbol_info = mt5.symbol_info(self.symbol)
        self.contract_size = self.symbol_info.trade_contract_size if self.symbol_info else 100.0
        
        # Single tick entry - no confirmation system needed
        self.required_confirmations = 0
        self.confirmation_window = 0
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.session_capital = 7149.74
        
    def log(self, message: str, color: str = Colors.RESET):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{color}[{timestamp}] {message}{Colors.RESET}")

    def get_candle_data(self):
        """Get current candle data with timestamp using shared utilities"""
        return TradingCore.get_candle_data(self.symbol, "M1")

    def get_market_data(self):
        """Get current market data and analysis"""
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            return None, None
            
        analysis = self.strategy.analyze_timeframe(self.timeframe)
        if not analysis:
            return None, None
            
        return tick, analysis

    def recover_position_data(self, pos):
        """Recover missing position data for positions opened before bot start"""
        ticket = pos.ticket
        direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        
        # Get entry candle data (approximation)
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 100)
        entry_candle_color = "UNKNOWN"
        entry_candle_time = datetime.fromtimestamp(pos.time)
        
        if rates is not None:
             # Find candle around entry time
             for rate in rates:
                 if rate['time'] <= pos.time:
                     entry_candle_color = 'GREEN' if rate['close'] > rate['open'] else 'RED'
                     # FIXED: Set entry_candle_time to the START of the candle, not the exact trade time
                     entry_candle_time = datetime.fromtimestamp(rate['time'])
        
        unified_pos_data = {
            'entry_price': pos.price_open,
            'reference_price': pos.price_open,
            'entry_time': datetime.fromtimestamp(pos.time),
            'direction': direction,
            'volume': pos.volume,
            'ut_trail_at_entry': 0, # Cannot easily recover historical UT trail
            'dollar_trail_active': False,
            'dollar_trail_sl': None,
            'phase_label': 'Recovered',
            'entry_candle_color': entry_candle_color,
            'entry_candle_time': entry_candle_time
        }
        
        self.position_data[ticket] = unified_pos_data
        self.strategy.open_positions[ticket] = unified_pos_data
        
        self.log(f"🔄 Recovered data for position #{ticket} ({direction}) | Candle: {entry_candle_color} at {entry_candle_time}", Colors.YELLOW)
        return unified_pos_data

    def is_sideways_market(self, ema7_array, lookback=SIDEWAYS_LOOKBACK, threshold=SIDEWAYS_THRESHOLD):
        """Detect sideways market using shared indicators and config"""
        return TechnicalIndicators.is_sideways_market(ema7_array, lookback, threshold)

    # Removed - not needed for single tick entry

    def check_entry_conditions(self, analysis):
        """Check if entry conditions are met - delegates to enhanced strategy"""
        # Check for existing positions first
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            return "NONE"  # Already in position
        
        # SIDEWAYS FILTER COMMENTED OUT (Depends on EMA 7)
        # ut_trail_array = analysis.get('ut_trail_array', [])
        # if self.is_sideways_market(ut_trail_array):
        #     return "SIDEWAYS"  # Block trades
            
        # Use enhanced strategy's entry logic (includes price action confirmation)
        entry_signal = self.strategy.check_entry_conditions(analysis)
        
        if entry_signal not in ["NONE", "SIDEWAYS"]:
            self.log(f"✅ {entry_signal} IMMEDIATE ENTRY - Price action confirmed!", Colors.GREEN)
            return entry_signal  # Execute immediately
        
        return entry_signal



    def execute_entry(self, signal, tick, analysis):
        """Execute trade entry with immediate trailing stop activation"""
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                self.log("Failed to get symbol info", Colors.RED)
                return False

            entry_price = tick.ask if signal == "BUY" else tick.bid
            volume = TradingCore.calculate_dynamic_volume(entry_price, self.symbol)
            
            # Skip trade if volume is too small
            if volume <= 0:
                self.log("Warning: Trade skipped - volume too small", Colors.RED)
                return False
            
            # Set broker SL initially - safer and visible in MT5
            if signal == "BUY":
                initial_sl = round(entry_price - self.fixed_sl_points, symbol_info.digits)
                take_profit = round(entry_price + self.tp_points, symbol_info.digits)
                order_type = mt5.ORDER_TYPE_BUY
                self.log(f"📐 BUY | Entry: {entry_price:.2f} | SL: {initial_sl:.2f} | TP: {take_profit:.2f}", Colors.CYAN)
            else:
                initial_sl = round(entry_price + self.fixed_sl_points, symbol_info.digits)
                take_profit = round(entry_price - self.tp_points, symbol_info.digits)
                order_type = mt5.ORDER_TYPE_SELL
                self.log(f"📐 SELL | Entry: {entry_price:.2f} | SL: {initial_sl:.2f} | TP: {take_profit:.2f}", Colors.CYAN)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": entry_price,
                "sl": initial_sl,  # ENABLED: Show SL in MT5
                "tp": take_profit,
                "magic": 123456,
                "comment": f"{signal}_BrokerSL",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.total_trades += 1
                conditions = f"RSI/{analysis.get('rsi', 0):.1f} Candle/{analysis.get('candle_color', '')}"
                
                # Print formatted trade entry box
                self.formatter.print_trade_entry(
                    signal, entry_price, volume, initial_sl, take_profit,
                    result.order, conditions, self.session_capital, self.total_trades
                )
                
                # Store position data in BOTH systems for sync (CRITICAL FIX)
                current_candle_color, current_candle_time = self.get_candle_data()
                if not current_candle_color or not current_candle_time:
                    # Fallback to analysis data
                    current_candle_color = analysis.get('candle_color', 'UNKNOWN')
                    current_candle_time = datetime.now()
                    self.log(f"⚠️ Using fallback candle data: {current_candle_color}", Colors.YELLOW)
                
                # Create unified position data
                unified_pos_data = {
                    'entry_price': entry_price,
                    'reference_price': entry_price,  # FIXED: Use entry price as reference for profit calculation
                    'entry_time': datetime.now(),
                    'direction': signal,
                    'volume': volume,  # Store volume for profit calculation
                    'ut_trail_at_entry': analysis.get('trail_stop', 0),
                    'dollar_trail_active': False,   # Starts in Phase 1 (Fixed 1pt SL)
                    'dollar_trail_sl': None,        # Set when 0.01pt profit reached
                    'phase_label': 'Fixed 1pt SL',   # Current phase label for display
                    'entry_candle_color': current_candle_color,  # Store entry candle color
                    'entry_candle_time': current_candle_time     # Store entry candle timestamp
                }
                
                # Store in BOTH systems using the SAME reference (CRITICAL FIX)
                self.position_data[result.order] = unified_pos_data
                self.strategy.open_positions[result.order] = unified_pos_data  # Same reference, not copy
                
                # Debug: Verify entry candle data is stored
                print(f"[ENTRY CANDLE DATA] #{result.order}: Color={current_candle_color}, Time={current_candle_time}")
                print(f"[ENTRY] Position #{result.order} created:")
                print(f"  Entry Price: {entry_price:.5f}")
                print(f"  Reference Price: {unified_pos_data['reference_price']:.5f}")
                print(f"  Direction: {signal}")
                print(f"  Entry Candle: {current_candle_color} at {current_candle_time}")
                
                self.log(f"✅ POSITION OPENED: $1 Reversal SL active. Trailing activates after +0.01pts profit", Colors.GREEN)
                
                # Draw initial lines on MT5 chart
                try:
                    # Get the actual position object for the ticket
                    new_positions = mt5.positions_get(ticket=result.order)
                    if new_positions:
                        MT5ChartLines.update_position_lines(self.symbol, new_positions, self.position_data)
                        print(f"[MT5 LINES] Initial lines drawn for position #{result.order}")
                except Exception as e:
                    print(f"[MT5 LINES ERROR] Failed to draw initial lines: {e}")
                
                return True
            else:
                error_msg = result.comment if result else 'Unknown error'
                self.log(f"❌ ORDER FAILED: {error_msg}", Colors.RED)
                return False
                
        except Exception as e:
            self.log(f"❌ Error executing trade: {e}", Colors.RED)
            return False



    def check_exit_conditions(self, tick, analysis):
        """FIXED: Unified exit system with proper reference price handling"""
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            return

        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info:
            return

        for pos in positions:
            ticket = pos.ticket
            # CRITICAL FIX: Don't use setdefault - it creates empty dict and loses data!
            # CRITICAL FIX: Recover data if missing (e.g. after bot restart)
            pos_data = self.position_data.get(ticket)
            if not pos_data:
                pos_data = self.recover_position_data(pos)
                
            # Debug position data every 20 ticks
            if self.tick_count % 20 == 0:
                ref_price = pos_data.get('reference_price')
                trail_active = pos_data.get('dollar_trail_active', False)
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                print(f"[STATUS] #{ticket} {direction}: Price={tick.bid if direction == 'BUY' else tick.ask:.5f}, Ref={ref_price:.5f}, Trail={trail_active}")
                
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"

            # STEP 1: Fixed Stop Loss (highest priority)
            def profit_callback(profit_points, exit_price):
                # Store for statistics
                pass
            
            if TradingCore.check_fixed_sl_exit(pos, tick, self.fixed_sl_points, profit_callback):
                if pos.ticket in self.position_data:
                    del self.position_data[pos.ticket]
                if pos.ticket in self.strategy.open_positions:
                    del self.strategy.open_positions[pos.ticket]
                continue
            
            # STEP 1.5: Opposite Candle Reversal Exit
            unified_pos_data = self.position_data.get(ticket, self.strategy.open_positions.get(ticket, {}))
            if TradingCore.check_opposite_candle_exit(pos, tick, unified_pos_data, self.symbol, self.reversal_exit_points, "M1"):
                # Cleanup from BOTH systems
                if pos.ticket in self.position_data:
                    del self.position_data[pos.ticket]
                if pos.ticket in self.strategy.open_positions:
                    del self.strategy.open_positions[pos.ticket]
                continue

            # STEP 2: Dynamic Trailing Stop
            try:
                dollar_trail_sl, trail_active, phase_label = TradingCore.calculate_trailing_stop_points(
                    pos, tick, pos_data, symbol_info, self.trailing_points, self.trailing_gap
                )
                
                # SYNC WITH BROKER: Update broker SL for safety
                if trail_active and dollar_trail_sl is not None:
                    broker_sl = pos.sl
                    should_update = False
                    if direction == "BUY" and (broker_sl == 0 or dollar_trail_sl > broker_sl + 0.01):
                        should_update = True
                    elif direction == "SELL" and (broker_sl == 0 or dollar_trail_sl < broker_sl - 0.01):
                        should_update = True
                            
                    if should_update:
                        if TradingCore.modify_position(ticket, self.symbol, dollar_trail_sl, pos.tp):
                            print(f"🔄 [TRAIL SYNC] SL moved to {dollar_trail_sl:.2f}")

            except Exception as e:
                print(f"[ERROR] Trailing stop error: {e}")


            
    def format_exit_condition(self, reason, pos, tick):
        """Format exit condition based on exit reason"""
        direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        
        if reason == "$1_Reversal":
            loss_pts = pos.price_open - tick.bid if direction == "BUY" else tick.ask - pos.price_open
            return f"$1 Reversal: -{loss_pts:.2f}pts loss"
        elif reason == "$1_Trail_Exit":
            return f"$1 Trailing Stop: Price hit trail SL"
        elif reason == "UT_Trail_Exit":
            return f"UT Trail Exit: Price crossed UT trail"
        elif reason == "TakeProfit":
            return f"Take Profit: +{self.tp_points}pts target reached"
        else:
            return f"Exit: {reason}"

    def display_status(self, tick, analysis):
        """Display clean single-line status with tick confirmation info"""
        self.tick_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        # Get position info
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            pos = positions[0]
            pos_data = self.position_data.get(pos.ticket, {})
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            
            # Calculate P/L correctly using contract size
            if direction == "BUY":
                pnl = (tick.bid - pos.price_open) * pos.volume * self.contract_size
            else:
                pnl = (pos.price_open - tick.ask) * pos.volume * self.contract_size
            
            # Determine active SL type accurately
            active_sl, sl_type_label = self.get_active_exit_level(tick, positions)
            sl_type = f"({sl_type_label})"
            
            # Colors for position display
            pnl_color = Colors.GREEN if pnl >= 0 else Colors.RED
            
            # Clean single-line format with exact colors (EMA7 Commented Out)
            print(f"[{timestamp}] {Colors.CYAN}Tick#{self.tick_count}{Colors.RESET} | "
                  f"Price: {Colors.ORANGE}{analysis['close']:.5f}{Colors.RESET} | "
                  f"Candle: {Colors.GREEN if analysis['candle_color'] == 'GREEN' else Colors.RED}{analysis['candle_color']}{Colors.RESET} | "
                  f"SL: {Colors.GREEN}{active_sl:.2f} {sl_type}{Colors.RESET} | "
                  f"RSI: {Colors.GREEN if analysis['rsi'] > 30 else Colors.RED}{analysis['rsi']:.1f}{Colors.RESET} | "
                  f"Status: {Colors.CYAN}IN POSITION{Colors.RESET} | "
                  f"P/L: {pnl_color}${pnl:.2f}{Colors.RESET}")
            return
        
        # When not in position - show entry status
        entry_signal = self.check_entry_conditions(analysis)
        
        if entry_signal == "SIDEWAYS":
            status = "SIDEWAYS"
            status_color = Colors.YELLOW
        elif entry_signal == "NONE":
            status = "WAITING"
            status_color = Colors.CYAN
        else:
            status = f"SIGNAL: {entry_signal}"
            status_color = Colors.MAGENTA
        
        print(f"[{timestamp}] {Colors.CYAN}Tick#{self.tick_count}{Colors.RESET} | "
              f"Price: {Colors.ORANGE}{analysis['close']:.5f}{Colors.RESET} | "
              f"Candle: {Colors.GREEN if analysis['candle_color'] == 'GREEN' else Colors.RED}{analysis['candle_color']}{Colors.RESET} | "
              f"RSI: {Colors.GREEN if analysis['rsi'] > 30 else Colors.RED}{analysis['rsi']:.1f}{Colors.RESET} | "
              f"Status: {status_color}{status}{Colors.RESET}")

    def get_active_exit_level(self, tick, positions):
        """Get the ACTUAL active exit level that will trigger position closure"""
        if not positions:
            return None, "No Position"
        
        pos = positions[0]
        pos_data = self.position_data.get(pos.ticket, {})
        direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
        
        # PRIORITY 1: Fixed 1-Point Stop Loss (ALWAYS ACTIVE)
        if direction == "BUY":
            fixed_sl = pos.price_open - 1.0
        else:
            fixed_sl = pos.price_open + 1.0
        
        # PRIORITY 2: Dynamic Trailing Stop (if active)
        trailing_sl = None
        if pos_data.get('dollar_trail_active', False):
            trailing_sl = pos_data.get('dollar_trail_sl')
        
        # Return the ACTIVE exit level (whichever will trigger first)
        if trailing_sl is not None:
            if direction == "BUY":
                # For BUY: Use the HIGHER of fixed SL or trailing SL (closer to current price)
                active_sl = max(fixed_sl, trailing_sl)
                if active_sl == trailing_sl:
                    return trailing_sl, "Dynamic Trailing SL"
                else:
                    return fixed_sl, "Fixed 1pt SL"
            else:  # SELL
                # For SELL: Use the LOWER of fixed SL or trailing SL (closer to current price)
                active_sl = min(fixed_sl, trailing_sl)
                if active_sl == trailing_sl:
                    return trailing_sl, "Dynamic Trailing SL"
                else:
                    return fixed_sl, "Fixed 1pt SL"
        else:
            return fixed_sl, "Fixed 1pt SL"

    def calculate_ut_trail(self, df, key_value=1.0):
        """UT Bot ATR trailing stop using shared indicators"""
        return TechnicalIndicators.calculate_ut_trail(df, key_value)

    def update_chart(self, tick, analysis):
        """FIXED: Display red dotted line showing ACTUAL active exit levels"""
        if not self.enable_chart or not self.ax:
            return
            
        try:
            # Get fresh data
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None or len(rates) < 10:
                print("[CHART] No data available")
                return
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate EMA 7 as base line
            ema7 = TechnicalIndicators.calculate_ema7(df['close'])
            if len(ema7) < 10:
                print("[CHART] Insufficient EMA7 data")
                return
            
            # Get positions
            positions = mt5.positions_get(symbol=self.symbol)
            
            # Create display array
            display_array = ema7.values.copy()
            exit_info = "EMA 7 Trend"
            
            # CRITICAL FIX: Show ACTUAL active exit level
            if positions:
                active_exit_level, exit_type = self.get_active_exit_level(tick, positions)
                if active_exit_level is not None:
                    # Override the ENTIRE line with the active exit level for visibility
                    display_array[-10:] = active_exit_level  # Last 10 points show exit level
                    exit_info = f"{exit_type}: {active_exit_level:.2f}"
            
            # Clear and plot
            self.ax.clear()
            
            # Plot price (blue line)
            x_range = range(len(df))
            self.ax.plot(x_range, df['close'], 'b-', linewidth=1.5, label='Price')
            
            # Plot RED DOTTED LINE (EMA 7 or Active Exit Level) - COMMENTED OUT
            # self.ax.plot(x_range, display_array, 'r:', linewidth=4, label=exit_info, alpha=1.0)
            
            # Current price marker
            current_price = df['close'].iloc[-1]
            self.ax.axhline(y=current_price, color='blue', linestyle='-', alpha=0.7, 
                          label=f'Price: {current_price:.2f}')
            
            # Position markers - MAKE STOP LOSS AND TAKE PROFIT MORE VISIBLE
            if positions:
                pos = positions[0]
                entry_color = 'green' if pos.type == mt5.POSITION_TYPE_BUY else 'red'
                self.ax.axhline(y=pos.price_open, color=entry_color, linestyle='-', alpha=0.8,
                              label=f'Entry: {pos.price_open:.2f}')
                
                # FIXED STOP LOSS - THICK RED DASHED LINE
                fixed_sl = pos.price_open - self.fixed_sl_points if pos.type == mt5.POSITION_TYPE_BUY else pos.price_open + self.fixed_sl_points
                self.ax.axhline(y=fixed_sl, color='red', linestyle='--', linewidth=3, alpha=1.0,
                              label=f'🔴 STOP LOSS: {fixed_sl:.2f}')
                
                # TAKE PROFIT - THICK GREEN DASHED LINE
                take_profit = pos.price_open + self.tp_points if pos.type == mt5.POSITION_TYPE_BUY else pos.price_open - self.tp_points
                self.ax.axhline(y=take_profit, color='green', linestyle='--', linewidth=3, alpha=1.0,
                              label=f'🟢 TAKE PROFIT: {take_profit:.2f}')
                
                # TRAILING STOP LOSS - ORANGE DASHED LINE
                pos_data = self.position_data.get(pos.ticket, {})
                if pos_data.get('dollar_trail_active', False):
                    trailing_sl = pos_data.get('dollar_trail_sl')
                    if trailing_sl:
                        self.ax.axhline(y=trailing_sl, color='orange', linestyle='--', linewidth=2, alpha=0.9,
                                      label=f'🟠 TRAILING SL: {trailing_sl:.2f}')
            
            # Chart formatting
            self.ax.set_title(f'{self.symbol} - RED DOTTED LINE = ACTIVE EXIT LEVEL', fontsize=12, fontweight='bold')
            self.ax.legend(loc='upper left', fontsize=9)
            self.ax.grid(True, alpha=0.3)
            
            # Force y-axis range to show all levels clearly
            if positions:
                pos = positions[0]
                y_center = pos.price_open
                y_range = 6.0  # Show ±6 points around entry for better visibility
                self.ax.set_ylim(y_center - y_range, y_center + y_range)
            
            # Update display
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
            # Debug confirmation - ENHANCED
            if positions:
                pos = positions[0]
                active_exit, exit_type = self.get_active_exit_level(tick, positions)
                fixed_sl = pos.price_open - 1.0 if pos.type == mt5.POSITION_TYPE_BUY else pos.price_open + 1.0
                take_profit = pos.price_open + 4.0 if pos.type == mt5.POSITION_TYPE_BUY else pos.price_open - 4.0
                print(f"[CHART] 🔴 STOP LOSS LINE: {fixed_sl:.2f}")
                print(f"[CHART] 🟢 TAKE PROFIT LINE: {take_profit:.2f}")
                print(f"[CHART] 🔵 RED DOTTED LINE: {exit_type} = {active_exit:.2f}")
                print(f"[CHART] Current Price: {current_price:.2f}")
            else:
                ema7_current = ema7.iloc[-1]
                print(f"[CHART] 🔵 RED DOTTED LINE = EMA 7: {ema7_current:.2f}")
            
        except Exception as e:
            print(f"[CHART ERROR] {e}")
            import traceback
            traceback.print_exc()
    def get_statistics(self):
        """Get trading statistics"""
        total = self.winning_trades + self.losing_trades
        win_rate = (self.winning_trades / total * 100) if total > 0 else 0
        session_time = (time.time() - self.session_start) / 60
        
        return f"""
TRADING STATISTICS:
Total Trades: {self.total_trades}
Winning Trades: {self.winning_trades}
Losing Trades: {self.losing_trades}
Win Rate: {win_rate:.1f}%
Total Profit: ${self.total_profit:.2f}
Session Time: {session_time:.1f} minutes
        """

    def run(self):
        """Main trading loop - CLEAN STRUCTURE"""
        # Test colors first
        print("Testing colors:")
        Colors.test_colors()
        print("\n" + "="*50 + "\n")
        
        self.log(">> Fixed Trading Bot Started", Colors.CYAN)
        self.log(f"Symbol: {self.symbol} | Timeframe: {self.timeframe}")
        self.log(f"Entry: Dual-Mode Strategy (Trend-Following + Counter-Trend Reversals) | Exit: $1 Reversal + $1 Trailing Stop")
        
        # Track previous positions to detect closures
        previous_positions = set()
        
        try:
            while True:
                # 1. GET MARKET DATA
                tick, analysis = self.get_market_data()
                if not tick or not analysis:
                    time.sleep(1)
                    continue

                # 2. CHECK FOR POSITION CLOSURES FIRST
                current_positions = mt5.positions_get(symbol=self.symbol)
                current_tickets = set(pos.ticket for pos in current_positions) if current_positions else set()
                
                # Detect closed positions
                closed_tickets = previous_positions - current_tickets
                for ticket in closed_tickets:
                    if ticket in self.position_data:
                        pos_data = self.position_data[ticket]
                        entry_time = pos_data.get('entry_time', datetime.now())
                        duration = str(datetime.now() - entry_time).split('.')[0]
                        direction = pos_data.get('direction', 'UNKNOWN')
                        entry_price = pos_data.get('entry_price', 0)
                        
                        # Get exit price from recent deals
                        deals = mt5.history_deals_get(position=ticket)
                        exit_price = entry_price  # fallback
                        if deals and len(deals) > 1:
                            exit_price = deals[-1].price  # last deal is the exit
                        
                        # Calculate profit for this trade
                        volume = pos_data.get('volume', 1.0)
                        profit_points = (exit_price - entry_price) if direction == 'BUY' else (entry_price - exit_price)
                        profit_dollars = profit_points * volume * self.contract_size
                        self.total_profit += profit_dollars
                        
                        if profit_points >= 0:
                            self.winning_trades += 1
                        else:
                            self.losing_trades += 1
                        
                        # Calculate statistics for display
                        total_closed = self.winning_trades + self.losing_trades
                        win_rate = (self.winning_trades / total_closed * 100) if total_closed > 0 else 0
                        
                        # Format exit condition
                        exit_condition = "Position Closed: Broker SL/TP or Manual"
                        
                        # Print formatted trade exit box
                        self.formatter.print_trade_exit_with_condition(
                            direction, entry_price, exit_price, duration, ticket,
                            total_closed, win_rate, self.session_capital, self.total_profit, exit_condition
                        )
                        
                        # Track profitable exits in strategy
                        if profit_points > 0:
                            self.strategy.last_profitable_exit_price = exit_price
                            self.strategy.last_profitable_direction = direction
                            self.log(f"✅ PROFITABLE EXIT TRACKED: {direction} exit at {exit_price:.2f} (+{profit_points:.2f}pts)", Colors.GREEN)
                        
                        # Cleanup from BOTH systems
                        del self.position_data[ticket]
                        if ticket in self.strategy.open_positions:
                            del self.strategy.open_positions[ticket]
                
                # Update previous positions
                previous_positions = current_tickets

                # 3. CHECK EXITS (for existing positions) - Use bot's own exit logic
                if current_positions:
                    self.check_exit_conditions(tick, analysis)

                # 4. CHECK ENTRIES (only if no positions) - immediate execution
                if not current_positions:
                    entry_signal = self.check_entry_conditions(analysis)
                    if entry_signal not in ["NONE", "SIDEWAYS"]:
                        self.execute_entry(entry_signal, tick, analysis)

                # 5. DISPLAY STATUS
                self.display_status(tick, analysis)

                # 6. UPDATE CHART (Red Dotted Line) - FORCE UPDATE
                if self.enable_chart:
                    self.update_chart(tick, analysis)
                
                # 7. UPDATE MT5 CHART LINES (Red Dotted Lines on MT5)
                try:
                    MT5ChartLines.update_position_lines(self.symbol, current_positions, self.position_data)
                except Exception as e:
                    print(f"[MT5 LINES ERROR] {e}")

                # 8. BRIEF PAUSE
                time.sleep(1)

        except KeyboardInterrupt:
            self.log("\n>> Bot stopped by user", Colors.YELLOW)
            self.log(self.get_statistics())
        except Exception as e:
            self.log(f">> Critical error: {e}", Colors.RED)
        finally:
            mt5.shutdown()

def main():
    """Initialize and run the fixed trading bot"""
    # Use shared MT5 connection
    if not MT5Connection.initialize_mt5():
        return
    
    # Create and run bot with chart enabled
    bot = TradingBot("XAUUSD", "M1", enable_chart=True)
    bot.run()

if __name__ == "__main__":
    main()