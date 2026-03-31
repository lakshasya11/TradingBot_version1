import MetaTrader5 as mt5
import time
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy
# Removed unused imports - all logic is now inline

def update_mt5_stop_loss(ticket, new_sl):
    """Update stop loss for existing position"""
    try:
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': ticket,
            'sl': round(new_sl, 5),
            'magic': 123456
        }
        result = mt5.order_send(request)
        return result and result.retcode == mt5.TRADE_RETCODE_DONE
    except Exception as e:
        print(f"[ERROR] Failed to update SL: {e}")
        return False

class TradeLogger:
    def __init__(self, session_capital=None):
        self.trades_executed = 0
        self.last_trade_time = None
        self.last_exit_time = None
        self.session_capital = session_capital  # Starting capital per session (configurable)
        self.current_capital = session_capital  # Current trading capital
        self.profits_reserved = 0.0    # Profits set aside
        self.candle_tick_count = 0     # Ticks within current candle
        self.entry_prices = {}         # Store entry prices for positions
        self.trades_this_candle = {}  # Track trades per candle
        self.candle_exit_occurred = {}  # Track if exit occurred in candle
        self.trade_volumes = {}      # Track volumes per trade
        self.previous_candle_structure = None  # Store previous candle structure
        self.candle_formation_progress = 0     # Track current candle formation %
        self.first_trade_exit_reason = {}  # Track exit reason per candle
        self.highest_profit_per_position = {}  # Track highest profit per position
        self.trailing_stop_per_position = {}   # Track trailing stop per position
        self.last_supertrend_direction = 0     # Track SuperTrend direction changes
        self.position_stop_loss = {}  # Track stop loss per position
        self.position_highest_price = {}  # Track highest price for BUY
        self.position_lowest_price = {}  # Track lowest price for SELL
        self.mt5_stop_loss = {}  # Track MT5 stop loss values
        self.trend_highest_price = 0.0      # Track highest price during bullish trend
        self.trend_lowest_price = 999999.0  # Track lowest price during bearish trend
        self.last_supertrend_direction = 0  # Track SuperTrend direction changes
        self.position_stop_loss = {}  # Track stop loss per position ticket
        self.trend_highest_price = 0.0
        self.trend_lowest_price = 999999.0
        self.supertrend_stop_loss = {}
        # Add these lines to TradeLogger.__init__ (around line 50)
        self.supertrend_up_high = {}      # Track highest price during bullish SuperTrend
        self.supertrend_down_low = {}     # Track lowest price during bearish SuperTrend
        self.high_water_mark_sl = {}      # High-water mark stop loss per position
        self.supertrend_stability_start = None  # When current direction started
        self.last_supertrend_direction = None   # Track direction changes
        self.trend_confirmed = False  # Track if current trend is confirmed
        self.position_entry_direction = {}  # Track SuperTrend direction when position was opened
        # Add these lines after line 50 in TradeLogger.__init__()
        self.trend_supertrend_values = []     # Store SuperTrend values for current trend
        self.current_trend_direction = 0      # Track current trend direction

        
        # ENHANCED PROFIT TRACKING
        self.total_profit = 0.0        # Total profit/loss accumulated
        self.winning_trades = 0        # Number of profitable trades
        self.losing_trades = 0         # Number of losing trades
        self.largest_win = 0.0         # Biggest single profit
        self.largest_loss = 0.0        # Biggest single loss
        self.trade_history = []        # Complete trade history

    def record_trade_for_candle(self, current_candle_time, position_ticket, volume):
        """Record trade for candle tracking"""
        if current_candle_time not in self.trades_this_candle:
            self.trades_this_candle[current_candle_time] = 0

        self.trades_this_candle[current_candle_time] += 1
        self.trade_volumes[position_ticket] = volume  # Store volume for this position

    # ADD THESE TWO NEW METHODS:
    def analyze_candle_structure(self, candle):
        """Analyze candle structure: bullish/bearish based on close vs open"""
        if candle['close'] > candle['open']:
            return "BULLISH"
        elif candle['close'] < candle['open']:
            return "BEARISH"
        else:
            return "DOJI"
    
    def calculate_candle_formation(self, current_candle, current_price):
        """Calculate how much of current candle has formed (0-100%)"""
        candle_range = current_candle['high'] - current_candle['low']
        if candle_range == 0:
            return 0
        price_movement = abs(current_price - current_candle['open'])
        formation_percentage = (price_movement / candle_range) * 100
        return min(formation_percentage, 100)  # Cap at 100%
    
    def calculate_candle_body_percentage(self, current_candle, current_price, previous_candle):
        """Calculate if current candle has built 50% of previous candle body"""
        prev_range = previous_candle['high'] - previous_candle['low']
        if prev_range == 0:
            return 0
        current_range = abs(current_price - current_candle['open'])
        return (current_range / prev_range) * 100
    
    def calculate_volume(self, current_price):
        """Calculate volume based on capital with broker minimum check"""
        if not self.current_capital or not current_price:
            return 0
        # Pure volume calculation: capital / (price * contract_size)
        contract_size = 100
        volume = self.current_capital / (current_price * contract_size)
        # Round to 2 decimal places
        volume = round(volume, 2)
        # Check broker minimum (typically 0.01 for XAUUSD)
        if volume < 0.01:
            return 0  # Return 0 to skip trade if insufficient capital
        
        return volume
        
    def log_trade(self, signal, price, volume):
        self.trades_executed += 1
        self.last_trade_time = datetime.now()
        
    def log_exit(self, profit_loss=0):
        self.last_exit_time = datetime.now()

        print(f"[DEBUG] Exit P/L: {profit_loss:.2f} | Capital Before: {self.current_capital:.2f}")  # ADD THIS
        
        # ENHANCED PROFIT CAPTURE
        self.total_profit += profit_loss
        
        if profit_loss > 0:
            self.winning_trades += 1
            self.profits_reserved += profit_loss  # Set profits aside
            if profit_loss > self.largest_win:
                self.largest_win = profit_loss
        else:
            self.losing_trades += 1
            self.current_capital += profit_loss   # Deduct losses from capital
            if profit_loss < self.largest_loss:
                self.largest_loss = profit_loss
        print(f"[DEBUG] Capital After: {self.current_capital:.2f}")  # ADD THIS
        
        # Store trade in history
        self.trade_history.append({
            'time': self.last_exit_time,
            'profit_loss': profit_loss,
            'type': 'WIN' if profit_loss > 0 else 'LOSS'
        })
            
    def can_trade(self, cooldown_seconds=60):
        if self.last_exit_time is None:
            return True
        return (datetime.now() - self.last_exit_time).total_seconds() > cooldown_seconds
        
    def get_stats(self):
        win_rate = (self.winning_trades / (self.winning_trades + self.losing_trades) * 100) if (self.winning_trades + self.losing_trades) > 0 else 0
        return f"\nPROFIT CAPTURE STATISTICS:\n   Total Trades: {self.trades_executed}\n   Total Profit: ${self.total_profit:.2f}\n   Win Rate: {win_rate:.1f}% ({self.winning_trades}W/{self.losing_trades}L)\n   Largest Win: ${self.largest_win:.2f}\n   Largest Loss: ${self.largest_loss:.2f}\n   Capital: ${self.current_capital:.2f}\n   Profits Reserved: ${self.profits_reserved:.2f}\n   Last Trade: {self.last_trade_time or 'None'}"
    
    def calculate_trend_extreme_sl(self, supertrend_direction, supertrend_value):
        """Calculate stop loss based on trend extremes"""
        # Reset when trend changes
        if self.current_trend_direction != supertrend_direction:
            self.current_trend_direction = supertrend_direction
            self.trend_supertrend_values = [supertrend_value]
        else:
            # Add current value to trend sequence
            self.trend_supertrend_values.append(supertrend_value)
        
        # Return extreme based on direction
        if supertrend_direction == 1:  # Bullish - highest value
            return max(self.trend_supertrend_values)
        else:  # Bearish - lowest value
            return min(self.trend_supertrend_values)

    def check_50_percent_reversal(self, current_candle, previous_candle, current_price, pos_type):
        """Check for 50% candle reversal exit condition"""
        # Calculate candle sizes
        prev_candle_size = abs(previous_candle['close'] - previous_candle['open'])
        current_candle_size = abs(current_price - current_candle['open'])
        
        # Avoid division by zero
        if prev_candle_size == 0:
            return False
        
        # Calculate percentage of current candle relative to previous
        reversal_percentage = (current_candle_size / prev_candle_size) * 100
        
        # Check reversal conditions
        if pos_type == "BUY":
            # BUY exit: Previous GREEN, Current RED, Current >= 50% of previous
            prev_green = previous_candle['close'] > previous_candle['open']
            current_red = current_price < current_candle['open']
            return prev_green and current_red and reversal_percentage >= 50.0
        
        else:  # SELL
            # SELL exit: Previous RED, Current GREEN, Current >= 50% of previous  
            prev_red = previous_candle['close'] < previous_candle['open']
            current_green = current_price > current_candle['open']
            return prev_red and current_green and reversal_percentage >= 50.0
    
    def check_supertrend_stability(self, current_direction):
        """Check if SuperTrend direction has been stable for 60+ seconds only after trend changes"""
        current_time = time.time()
        
        if self.last_supertrend_direction != current_direction:
            # Trend changed - reset stability and confirmation
            self.supertrend_stability_start = current_time
            self.last_supertrend_direction = current_direction
            self.trend_confirmed = False
            return False, 0
        
        # If trend already confirmed, no need to wait
        if self.trend_confirmed:
            return True, 999  # Return high duration to show confirmed
        
        # Check if 30 seconds have passed since trend change
        if self.supertrend_stability_start:
            stability_duration = current_time - self.supertrend_stability_start
            if stability_duration >= 60.0:
                self.trend_confirmed = True
                return True, stability_duration
            return False, stability_duration
        
        return False, 0

    def can_enter_new_trade(self, current_candle_time, symbol="XAUUSD"):
        """Check if we can enter a new trade (max 2 per candle if exit occurred)"""
        # Check existing positions - only 1 at a time
        existing_positions = mt5.positions_get(symbol=symbol)
        if existing_positions and len(existing_positions) > 0:
            return False  # Only 1 trade at a time

        # Initialize candle tracking
        if current_candle_time not in self.trades_this_candle:
            self.trades_this_candle[current_candle_time] = 0
        if current_candle_time not in self.candle_exit_occurred:
            self.candle_exit_occurred[current_candle_time] = False

        # Trade limit logic: Only 1 trade per candle
        current_trades = self.trades_this_candle[current_candle_time]
        return current_trades == 0  # Only allow if no trades this candle

def complete_entry_analysis():
    load_dotenv()
    
    # MT5 Connection
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    if not mt5.login(mt5_login, mt5_pass, mt5_server):
        print(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    # Initialize components
    symbol = "XAUUSD"
    strategy = EnhancedTradingStrategy(symbol, "M1")
    
    # Default capital set to $2500
    session_capital = 25000.0  # $2,5000 capital - CHANGE THIS VALUE AS NEEDED
    logger = TradeLogger(session_capital)
    
    print(f"\n[ZERO-LATENCY TRADING SYSTEM ACTIVE]")
    print(f"Symbol: {symbol} | SuperTrend: Period=10, Multiplier=0.7")
    print(f"Entry: BUY(RSI>30,ST=1,Green) | SELL(RSI<70,ST=-1,Red)")
    print(f"Exit: Dynamic Stop Loss (Trend Extremes) + SuperTrend Reversal")
    print("="*80)
    
    tick_count = 0
    start_time = time.time()
    last_tick_time = None
    
    try:
        while True:
            tick_count += 1
            current_time = datetime.now(pytz.timezone('Europe/Athens'))  # EET timezone
            time_display = current_time.strftime("%H:%M:%S.%f")[:-3]
            
            # Get fresh tick data
            tick = mt5.symbol_info_tick(symbol)
            if tick and (last_tick_time is None or tick.time != last_tick_time):
                last_tick_time = tick.time
                # Use bid price as current price (more reliable than tick.last)
                current_price = tick.bid if tick.bid > 0 else tick.ask
                
                # Get market data
                market_data = {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': tick.ask - tick.bid,
                    'volume': tick.volume
                }
                
                # Get analysis data
                analysis = strategy.analyze_timeframe("M1")
                if analysis:
                    # Extract indicators with SuperTrend prominence
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    supertrend_direction = analysis.get('supertrend_direction', 0)  # MOST PROMINENT
                    atr = analysis.get('atr', 0)
                    supertrend_direction = analysis.get('supertrend_direction', 0)  # MOST PROMINENT
                    supertrend_sl_value = analysis.get('supertrend_sl_value', 0)  # NEW: For SELL stop loss
                    atr = analysis.get('atr', 0)
  
                    # Get current candle data + intra-candle analysis
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
                    if rates is not None and len(rates) >= 2:
                        current_candle = rates[-1]
                        previous_candle = rates[-2]
                        
                        # INTRA-CANDLE ANALYSIS: Track ticks within candle
                        current_candle_time = current_candle['time']
                        if not hasattr(logger, 'last_candle_time') or logger.last_candle_time != current_candle_time:
                            logger.last_candle_time = current_candle_time
                            logger.candle_tick_count = 0  # Reset for new candle
                        logger.candle_tick_count += 1
                        
                        # STRUCTURE ANALYSIS: Previous candle structure
                        prev_structure = logger.analyze_candle_structure(previous_candle)
                        logger.previous_candle_structure = prev_structure
                        
                       
                        
                        # ENHANCED ENTRY LOGIC: RSI + SuperTrend + Current Direction + Candle Color
                        structure_signal = None
                        current_candle_color = "GREEN" if current_price > current_candle['open'] else "RED"

                        if rsi > 30 and supertrend_direction == 1 and current_candle_color == "GREEN":
                            structure_signal = "BUY"
                        elif rsi < 70 and supertrend_direction == -1 and current_candle_color == "RED":
                            structure_signal = "SELL"

                                            
                        # Current candle direction confirmation (already covered by candle color check)
                        structure_confirmed = structure_signal is not None

                        
                        # FINAL SIGNAL
                        if structure_signal and structure_confirmed:
                            signal = structure_signal
                            entry_conditions_met = True
                        else:
                            signal = "NONE"
                            entry_conditions_met = False

                        # Get symbol info for tick size
                        symbol_info = mt5.symbol_info(symbol)
                        tick_size = symbol_info.trade_tick_size if symbol_info else 0.01
                        
                        # ENTRY EXECUTION: Simplified validation
                        if entry_conditions_met and current_price > 0 and atr > 0:
                            volume = logger.calculate_volume(current_price)
                            if volume > 0:
                                order_ready = True
                                if signal == "BUY":
                                    entry_price = market_data['ask'] + tick_size
                                else:  # SELL
                                    entry_price = market_data['bid'] - tick_size
                            else:
                                order_ready = False
                                entry_price = 0
                        else:
                            order_ready = False
                            entry_price = 0
                         
                        # Check SuperTrend stability before final execution
                        is_stable, stability_duration = logger.check_supertrend_stability(supertrend_direction)
                        all_systems_go = order_ready and is_stable

                        
                        # ========== NEW EXIT CONDITIONS ==========
                        existing_positions = mt5.positions_get(symbol=symbol)
                        if existing_positions:
                            # Track trend extremes GLOBALLY (not per position)
                            if supertrend_direction == 1:  # Bullish trend
                                if current_price > logger.trend_highest_price:
                                    logger.trend_highest_price = current_price
                            elif supertrend_direction == -1:  # Bearish trend
                                if current_price < logger.trend_lowest_price:
                                    logger.trend_lowest_price = current_price
                            
                            # Check for trend direction change
                            if logger.last_supertrend_direction != 0 and logger.last_supertrend_direction != supertrend_direction:
                                print(f"[TREND_CHANGE] SuperTrend changed from {logger.last_supertrend_direction} to {supertrend_direction}")
                                # Reset trend extremes on direction change
                                if supertrend_direction == 1:
                                    logger.trend_highest_price = current_price
                                    logger.trend_lowest_price = 999999.0
                                else:
                                    logger.trend_lowest_price = current_price
                                    logger.trend_highest_price = 0.0
                            
                            logger.last_supertrend_direction = supertrend_direction
                            # Track trend extremes every tick
                            if supertrend_direction == 1:
                                if current_price > logger.trend_highest_price:
                                    logger.trend_highest_price = current_price
                            elif supertrend_direction == -1:
                                if current_price < logger.trend_lowest_price:
                                    logger.trend_lowest_price = current_price

                            
                            # TREND EXTREME STOP LOSS CALCULATION
                            supertrend_value = analysis.get('supertrend_value', 0)
                            trend_extreme_sl = logger.calculate_trend_extreme_sl(supertrend_direction, supertrend_value)

                            for pos in existing_positions:
                                pos_type = "BUY" if pos.type == 0 else "SELL"
                                pos_ticket = pos.ticket
                                
                                # Use trend extreme as stop loss
                                stop_loss_value = trend_extreme_sl
                                
                                # Update MT5 stop loss every tick
                                if stop_loss_value > 0:
                                    update_mt5_stop_loss(pos_ticket, stop_loss_value)
                                    logger.high_water_mark_sl[pos_ticket] = stop_loss_value

                                
                                # Exit conditions: Check both trend reversal AND dynamic stop loss in parallel
                                should_exit = False
                                exit_reasons = []

                                # Check trend reversal exit
                                if pos_ticket in logger.position_entry_direction:
                                    entry_direction = logger.position_entry_direction[pos_ticket]
                                    if entry_direction != supertrend_direction:
                                        should_exit = True
                                        exit_reasons.append("Trend Reversal")

                                # Check trend extreme stop loss exit
                                if pos_type == "BUY" and current_price <= stop_loss_value:
                                    should_exit = True
                                    exit_reasons.append("Trend Extreme SL Cross")
                                elif pos_type == "SELL" and current_price >= stop_loss_value:
                                    should_exit = True
                                    exit_reasons.append("Trend Extreme SL Cross")

                                # Check 50% candle reversal exit
                                if logger.check_50_percent_reversal(current_candle, previous_candle, current_price, pos_type):
                                    should_exit = True
                                    exit_reasons.append("50% Candle Reversal")

                                # Combine exit reasons
                                exit_reason = " + ".join(exit_reasons) if exit_reasons else ""

                                
                                if should_exit:
                                    # Execute exit
                                    close_type = mt5.ORDER_TYPE_SELL if pos_type == "BUY" else mt5.ORDER_TYPE_BUY
                                    result = mt5.order_send({
                                        'action': mt5.TRADE_ACTION_DEAL,
                                        'symbol': symbol,
                                        'volume': pos.volume,
                                        'type': close_type,
                                        'position': pos.ticket,
                                        'type_filling': mt5.ORDER_FILLING_IOC,
                                        'magic': 123456
                                    })
                                    
                                    print(f"\n{'='*60}")
                                    print(f"[POSITION CLOSED] {pos_type} | P/L: ${pos.profit:.2f}")
                                    print(f"Exit Reason: {exit_reason}")

                                    print(f"{'='*60}")
                                    logger.log_exit(pos.profit)
                                    
                                    # Cleanup
                                    if pos_ticket in logger.high_water_mark_sl:
                                        del logger.high_water_mark_sl[pos_ticket]
                                    break

                                                             
                        # Organized terminal display
                        if existing_positions:
                            # Show detailed info every 5th tick when in position
                            if tick_count % 5 == 0:
                                print(f"\n{'='*80}")
                                print(f"[{time_display}] POSITION MONITORING")
                                print(f"{'='*80}")
                                for pos in existing_positions:
                                    pos_type = 'BUY' if pos.type == 0 else 'SELL'
                                    pos_ticket = pos.ticket
                                    supertrend_val = analysis.get('supertrend_value', 0)
                                    print(f"Position #{pos_ticket} ({pos_type})")
                                    print(f"  Current Price: {current_price:.5f}")
                                    # Show dynamic stop loss type
                                    is_stable_display, _ = logger.check_supertrend_stability(supertrend_direction)
                                    if is_stable_display:
                                        sl_type_display = "SuperTrend"
                                        current_sl = supertrend_val
                                    else:
                                        # Show correct candle extreme based on position type
                                        if pos_type == 'BUY':
                                            sl_type_display = "Candle Low"
                                            current_sl = current_candle['low']
                                        else:  # SELL
                                            sl_type_display = "Candle High"
                                            current_sl = current_candle['high']

                                    print(f"  Dynamic SL ({sl_type_display}): {current_sl:.5f}")

                                    print(f"  P/L: ${pos.profit:.2f}")
                                    print(f"  Distance to SL: {abs(current_price - current_sl):.5f}")
                                
                                print(f"\nMARKET CONDITIONS:")
                                print(f"  RSI: {rsi:.1f} | SuperTrend Direction: {supertrend_direction} | Signal: {signal}")
                                
                                current_candle_color = "GREEN" if current_price > current_candle['open'] else "RED"
                                print(f"\nENTRY CONDITIONS STATUS:")
                                buy_rsi = "✓" if rsi > 30 else "✗"
                                buy_st = "✓" if supertrend_direction == 1 else "✗"
                                buy_candle = "✓" if current_candle_color == "GREEN" else "✗"
                                sell_rsi = "✓" if rsi < 70 else "✗"
                                sell_st = "✓" if supertrend_direction == -1 else "✗"
                                sell_candle = "✓" if current_candle_color == "RED" else "✗"
                                
                                print(f"  BUY:  RSI>30 {buy_rsi} | ST=1 {buy_st} | GREEN {buy_candle}")
                                print(f"  SELL: RSI<70 {sell_rsi} | ST=-1 {sell_st} | RED {sell_candle}")
                                stability_status = "✓" if is_stable else f"✗ ({stability_duration:.1f}s/60s)"
                                print(f"  STABILITY: ST Stable 60s {stability_status}")

                                print(f"{'='*80}")
                        else:
                            # When no positions, show entry conditions every 20th tick
                            if tick_count % 20 == 0:
                                print(f"\n{'='*80}")
                                print(f"[{time_display}] WAITING FOR ENTRY SIGNAL")
                                print(f"{'='*80}")
                                print(f"MARKET DATA:")
                                print(f"  Price: {current_price:.5f}")
                                print(f"  RSI: {rsi:.1f}")
                                print(f"  SuperTrend Direction: {supertrend_direction}")
                                print(f"  Current Signal: {signal}")
                                
                                current_candle_color = "GREEN" if current_price > current_candle['open'] else "RED"
                                print(f"\nENTRY CONDITIONS STATUS:")
                                buy_rsi = "✓" if rsi > 30 else "✗"
                                buy_st = "✓" if supertrend_direction == 1 else "✗"
                                buy_candle = "✓" if current_candle_color == "GREEN" else "✗"
                                sell_rsi = "✓" if rsi < 70 else "✗"
                                sell_st = "✓" if supertrend_direction == -1 else "✗"
                                sell_candle = "✓" if current_candle_color == "RED" else "✗"
                                
                                print(f"  BUY:  RSI>30 {buy_rsi} | ST=1 {buy_st} | GREEN {buy_candle}")
                                print(f"  SELL: RSI<70 {sell_rsi} | ST=-1 {sell_st} | RED {sell_candle}")
                                stability_status = "✓" if is_stable else f"✗ ({stability_duration:.1f}s/60s)"
                                print(f"  STABILITY: ST Stable 60s {stability_status}")
                                print(f"{'='*80}")
                            
                        # STRICT EXECUTION: Absolutely max 1 per candle
                        if all_systems_go and logger.can_enter_new_trade(current_candle_time, symbol):
                            # Double-check trade count before execution
                            current_trades = logger.trades_this_candle.get(current_candle_time, 0)
                            if current_trades >= 1:
                                continue  # Skip if already traded this candle
                                
                            print(f"[DEBUG] Candle: {current_candle_time} | Trades this candle: {current_trades}")
                            # Calculate volume once and keep it consistent for this trade
                            volume = logger.calculate_volume(current_price)
    
                            if volume > 0:  # Only trade if sufficient capital
                                # IMMEDIATELY reserve candle slot BEFORE sending order
                                if current_candle_time not in logger.trades_this_candle:
                                    logger.trades_this_candle[current_candle_time] = 0
                                logger.trades_this_candle[current_candle_time] += 1
                                
                                execution_start = time.time()
                                # Calculate initial stop loss using trend extreme
                                initial_sl = logger.calculate_trend_extreme_sl(supertrend_direction, supertrend_value)

                                result = mt5.order_send({
                                    'action': mt5.TRADE_ACTION_DEAL,
                                    'symbol': symbol,
                                    'volume': volume,
                                    'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                                    'sl': initial_sl,
                                    'type_filling': mt5.ORDER_FILLING_IOC,
                                    'magic': 123456
                                })

                                execution_time = (time.time() - execution_start) * 1000

                                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                    # Success - get position details
                                    time.sleep(0.1)  # Small delay to ensure position is created
                                    positions = mt5.positions_get(symbol=symbol)
                                    if positions:
                                        position_ticket = positions[-1].ticket  # Get the newest position
                                        logger.record_trade_for_candle(current_candle_time, position_ticket, volume)
                                        logger.trade_volumes[position_ticket] = volume  # Ensure volume is stored
                                        
                                        # INITIALIZE STOP LOSS TRACKING
                                        logger.position_stop_loss[position_ticket] = current_price
                                        logger.position_highest_price[position_ticket] = current_price
                                        logger.position_lowest_price[position_ticket] = current_price
                                        logger.position_entry_direction[position_ticket] = supertrend_direction  # ADD THIS LINE

                                        
                                    logger.log_trade(signal, result.price, volume)

                                    candle_trade_count = logger.trades_this_candle.get(current_candle_time, 0)
                                    print(f"\n{'='*60}")
                                    print(f"[TRADE EXECUTED] {signal} at {result.price:.5f}")
                                    print(f"Volume: {volume} | Trade: {candle_trade_count}/1")
                                    print(f"Capital: ${logger.current_capital:.2f} | Reserved: ${logger.profits_reserved:.2f}")
                                    print(f"{'='*60}")
                                else:
                                    # Failed - DO NOT rollback the count to prevent retry
                                    error_msg = result.comment if result else "Unknown error"
                                    print(f"\n{'='*60}")
                                    print(f"[TRADE FAILED] {signal} - {error_msg}")
                                    print(f"Execution Time: {execution_time:.1f}ms")
                                    print(f"Candle slot remains reserved to prevent retry")
                                    print(f"{'='*60}")

                            else:
                                print(f"\n[INSUFFICIENT CAPITAL] Cannot execute {signal} trade")
                                print(f"Required Volume: {volume} | Available Capital: ${logger.current_capital:.2f}")

                        
                        time.sleep(0)  # ZERO delay for absolute maximum speed
                        
                        # Enhanced stop loss display with SuperTrend line
                        stop_loss_display = "None"
                        if existing_positions:
                            supertrend_val = analysis.get('supertrend_value', 0)
                            if supertrend_val > 0:
                                stop_loss_display = f"{supertrend_val:.5f}"

                        print(f"\r[LIVE] Price={current_price:.5f} | SL={stop_loss_display} | ST_Dir={supertrend_direction} | Tick#{tick_count} | Capital=${logger.current_capital:.2f} | Profit=${logger.total_profit:.2f}", end='', flush=True)

    except KeyboardInterrupt:
        print(f"\n\nSystem stopped by user")
        print(logger.get_stats())
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    complete_entry_analysis()