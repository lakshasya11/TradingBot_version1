"""
Trading Core Module - Core trading functions and utilities
Handles position management, volume calculation, and exit logic
"""
import MetaTrader5 as mt5
from datetime import datetime

class TradingCore:
    """Core trading functions used across all strategies"""
    
    @staticmethod
    def get_candle_data(symbol: str, timeframe: str = "M1"):
        """FIXED: Get current FORMING candle data for proper entry tracking"""
        timeframe_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        
        tf_const = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
        
        # Get current forming candle for entry tracking
        rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 1)
        if rates is None or len(rates) < 1:
            print(f"[CANDLE_DATA] Failed to get candle data for {symbol} {timeframe}")
            return None, None
        
        import pandas as pd
        
        # Use the current forming candle for entry tracking
        current_candle = rates[-1]  # Most recent candle (forming)
        candle_color = 'GREEN' if current_candle['close'] > current_candle['open'] else 'RED'
        candle_time = pd.to_datetime(current_candle['time'], unit='s')
        
        # Debug logging
        print(f"[ENTRY CANDLE] {symbol} {timeframe}: {candle_color} candle at {candle_time} (CURRENT FORMING)")
        
        return candle_color, candle_time
    
    @staticmethod
    def calculate_dynamic_volume(entry_price: float, symbol: str, capital_cap: float = 5000.0) -> float:
        """Calculate dynamic volume based on account balance, capped at capital usage"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return 0.01
            
            balance = account_info.balance
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.01
            
            # Calculate volume based on balance/price ratio, capped at capital_cap
            max_capital_usage = min(balance, capital_cap)
            volume = max_capital_usage / entry_price
            
            # Round to valid volume step
            volume_step = symbol_info.volume_step
            volume = round(volume / volume_step) * volume_step
            
            # Ensure within broker limits
            min_volume = symbol_info.volume_min
            max_volume = symbol_info.volume_max
            volume = max(min_volume, min(max_volume, volume))
            
            return volume
        except Exception:
            return 0.01
    
    @staticmethod
    def check_fixed_sl_exit(pos, tick, fixed_sl_points: float, profit_callback=None) -> bool:
        """Check if position should exit due to fixed stop loss"""
        try:
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            
            if direction == "BUY":
                # BUY: Exit when bid <= entry - fixed_sl_points
                fixed_sl_level = pos.price_open - fixed_sl_points
                if tick.bid <= fixed_sl_level:
                    exit_price = tick.bid
                    profit_points = exit_price - pos.price_open
                    
                    print(f"[FIXED SL EXIT] FIXED SL EXIT: BUY #{pos.ticket} | {tick.bid:.2f} <= {fixed_sl_level:.2f} | P/L: {profit_points:.2f}pts")
                    
                    # Close position
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": mt5.ORDER_TYPE_SELL,
                        "position": pos.ticket,
                        "magic": 123456,
                        "comment": "Fixed_SL_Exit",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    result = mt5.order_send(close_request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        if profit_callback:
                            profit_callback(profit_points, exit_price)
                        return True
            
            else:  # SELL
                # SELL: Exit when ask >= entry + fixed_sl_points
                fixed_sl_level = pos.price_open + fixed_sl_points
                if tick.ask >= fixed_sl_level:
                    exit_price = tick.ask
                    profit_points = pos.price_open - exit_price
                    
                    print(f"[FIXED SL EXIT] FIXED SL EXIT: SELL #{pos.ticket} | {tick.ask:.2f} >= {fixed_sl_level:.2f} | P/L: {profit_points:.2f}pts")
                    
                    # Close position
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": mt5.ORDER_TYPE_BUY,
                        "position": pos.ticket,
                        "magic": 123456,
                        "comment": "Fixed_SL_Exit",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    result = mt5.order_send(close_request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        if profit_callback:
                            profit_callback(profit_points, exit_price)
                        return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Error in check_fixed_sl_exit: {e}")
            return False
    
    @staticmethod
    def calculate_trailing_stop_points(pos, tick, pos_data, symbol_info, trailing_points: float, trailing_gap: float):
        """FIXED: Calculate dynamic trailing stop with PROGRESSIVE GAP REDUCTION"""
        try:
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            
            # CRITICAL FIX: Use stored reference price from entry, NOT current tick
            reference_price = pos_data.get('reference_price')
            if reference_price is None:
                # FALLBACK: If no stored reference price, use entry price as reference
                reference_price = pos.price_open
                pos_data['reference_price'] = reference_price
                print(f"[TRAIL INIT] #{pos.ticket}: Reference price set to {reference_price:.5f} (ENTRY PRICE {direction})")
            
            # Calculate current profit in points using PRESERVED reference price
            if direction == "BUY":
                profit_points = tick.bid - reference_price  # Current bid vs entry reference
            else:  # SELL
                profit_points = reference_price - tick.ask  # Entry reference vs current ask
            
            # Check if trailing should be active
            trail_active = profit_points >= trailing_points
            
            if trail_active:
                # DYNAMIC GAP CALCULATION - Progressive tightening
                dynamic_gap = TradingCore.calculate_dynamic_gap(profit_points)
                
                # Calculate new trailing stop level with dynamic gap
                if direction == "BUY":
                    new_trailing_sl = round(tick.bid - dynamic_gap, symbol_info.digits)
                    phase_label = f"Trail: bid-{dynamic_gap:.1f}"
                else:  # SELL
                    new_trailing_sl = round(tick.ask + dynamic_gap, symbol_info.digits)
                    phase_label = f"Trail: ask+{dynamic_gap:.1f}"
                
                # Implement proper ratcheting (only move in favorable direction)
                current_best_sl = pos_data.get('dollar_trail_sl')
                
                if current_best_sl is None:
                    # First time activation - set initial trailing SL
                    pos_data['dollar_trail_active'] = True
                    pos_data['dollar_trail_sl'] = new_trailing_sl
                    pos_data['phase_label'] = phase_label
                    print(f"[TRAIL ACTIVATED] {direction} #{pos.ticket}: Profit={profit_points:.3f}pts >= {trailing_points}pts | Initial SL={new_trailing_sl:.5f}")
                    return new_trailing_sl, True, phase_label
                else:
                    # Ratcheting logic - only move in favorable direction
                    should_update = False
                    if direction == "BUY" and new_trailing_sl > current_best_sl:
                        should_update = True  # Only move UP for BUY
                        print(f"[TRAIL RATCHET] BUY #{pos.ticket}: SL moves UP {current_best_sl:.5f} -> {new_trailing_sl:.5f}")
                    elif direction == "SELL" and new_trailing_sl < current_best_sl:
                        should_update = True  # Only move DOWN for SELL
                        print(f"[TRAIL RATCHET] SELL #{pos.ticket}: SL moves DOWN {current_best_sl:.5f} -> {new_trailing_sl:.5f}")
                    
                    if should_update:
                        pos_data['dollar_trail_sl'] = new_trailing_sl
                        pos_data['phase_label'] = phase_label
                        return new_trailing_sl, True, phase_label
                    else:
                        # Keep existing SL (no movement)
                        return current_best_sl, True, pos_data.get('phase_label', phase_label)
            else:
                # Not enough profit yet - show progress
                needed_profit = trailing_points - profit_points
                phase_label = f"Need +{needed_profit:.3f}pts for trail (Current: {profit_points:.3f}pts)"
                return None, False, phase_label
                
        except Exception as e:
            print(f"[ERROR] Error in calculate_trailing_stop_points: {e}")
            return None, False, "Error"
    
    @staticmethod
    def calculate_dynamic_gap(profit_points: float) -> float:
        """Calculate dynamic trailing gap that tightens as profit increases"""
        # Progressive gap reduction based on profit levels
        if profit_points >= 3.0:    # 3+ points profit
            return 0.4  # 0.4 point gap
        elif profit_points >= 2.0:  # 2+ points profit  
            return 0.6  # 0.6 point gap
        elif profit_points >= 1.0:  # 1+ points profit
            return 0.8  # 0.8 point gap
        else:  # 0.01 - 0.99 points profit
            return 1.0  # 1.0 point gap (initial)
    
    @staticmethod
    def modify_position(ticket: int, symbol: str, new_sl: float, new_tp: float) -> bool:
        """Modify position stop loss and take profit"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": new_sl,
                "tp": new_tp,
                "magic": 123456,
            }
            
            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            print(f"❌ Error modifying position #{ticket}: {e}")
            return False

    @staticmethod
    def check_opposite_candle_exit(pos, tick, pos_data, symbol, opposite_candle_exit_points=0.5, base_timeframe="M1") -> bool:
        """AGGRESSIVE EXIT: Exit if price reverses 0.5pts from the CURRENT candle's open"""
        try:
            import pandas as pd
            entry_candle_time = pos_data.get('entry_candle_time')
            
            # 1. Handle missing entry data (e.g. after bot restart)
            if not entry_candle_time:
                entry_candle_time = pd.to_datetime(pos.time, unit='s')
            
            # Normalize entry_candle_time
            if hasattr(entry_candle_time, 'replace'):
                entry_candle_time_norm = entry_candle_time.replace(second=0, microsecond=0)
            else:
                entry_candle_time_norm = pd.to_datetime(entry_candle_time).replace(second=0, microsecond=0)

            # 2. Get CURRENT FORMING candle data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
            if rates is None or len(rates) < 1:
                return False
            
            current_candle = rates[-1]
            current_candle_time = pd.to_datetime(current_candle['time'], unit='s')
            current_candle_high = current_candle['high']
            current_candle_low = current_candle['low']
            
            direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
            current_price = tick.bid if direction == "BUY" else tick.ask
            
            # 3. Calculate reversal from the candle's BEST point (High for BUY, Low for SELL)
            # AND Check if the reversal exit should be active (only after +0.5 profit)
            current_profit = (current_price - pos.price_open) if direction == "BUY" else (pos.price_open - current_price)
            
            # Check if reversal protection is already active or should be activated
            reversal_was_active = pos_data.get('reversal_protection_active', False)
            if not reversal_was_active and current_profit >= 0.5:
                pos_data['reversal_protection_active'] = True
                print(f"🛡️ [REVERSAL ACTIVE] #{pos.ticket}: Profit reached {current_profit:.2f}. Reversal protection is now LIVE.")
                reversal_was_active = True
            
            if not reversal_was_active:
                return False

            if direction == "BUY":
                reversal_points = current_candle_high - current_price
                ref_point = current_candle_high
            else:
                reversal_points = current_price - current_candle_low
                ref_point = current_candle_low

            # 4. AGGRESSIVE DEBUG: Show reversal on every tick
            if abs(reversal_points) > 0.01: 
                ref_label = "High" if direction == "BUY" else "Low"
                print(f"🔍 [EXIT WATCH] #{pos.ticket} {direction} | Price: {current_price:.2f} | {ref_label}: {ref_point:.2f} | Rev: {reversal_points:.3f} | Goal: {opposite_candle_exit_points}")

            # 5. Trigger Exit if reversal >= 0.5
            if reversal_points >= opposite_candle_exit_points:
                exit_price = current_price
                profit_points = (exit_price - pos.price_open) if direction == "BUY" else (pos.price_open - exit_price)
                
                print(f"💥 [REVERSAL EXIT] {direction} #{pos.ticket}: Price {current_price:.2f} reversed {reversal_points:.3f}pts from {ref_label} {ref_point:.2f} | P/L: {profit_points:.2f}pts")
                
                # Close position
                close_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if direction == "BUY" else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "price": tick.bid if direction == "BUY" else tick.ask,
                    "deviation": 10,
                    "magic": 123456,
                    "comment": f"Rev_0.5pt_HiLo",
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(close_request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    return True
            
            return False
            
        except Exception as e:
            print(f"[ERROR] Error in check_opposite_candle_exit: {e}")
            import traceback
            traceback.print_exc()
            return False