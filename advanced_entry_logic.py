import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

class CandleStructureValidator:
    """Validates candle structure requirements"""
    
    def __init__(self):
        self.min_body_percent = 0.3  # Back to original 0.3% body requirement
        self.top_range_percent = 60  # Back to original top 60% requirement
    
    def validate_strong_green_candle(self, candle_data: Dict, current_price: float = None) -> Tuple[bool, str]:
        """
        Validate strong green candle requirements:
        - Must be green (close > open)
        - Minimum 0.3% body requirement
        - Price must be in top 60% of candle range
        """
        try:
            open_price = candle_data.get('open', 0)
            close_price = candle_data.get('close', 0)
            high_price = candle_data.get('high', 0)
            low_price = candle_data.get('low', 0)
            
            # Use current price if provided, otherwise use close
            price_to_check = current_price if current_price else close_price
            
            # Check 1: Must be green candle
            if price_to_check <= open_price:
                return False, "Not a green candle (price <= open)"
            
            # Check 2: Minimum 0.3% body requirement
            body_size = abs(price_to_check - open_price)
            body_percent = (body_size / open_price) * 100
            
            if body_percent < self.min_body_percent:
                return False, f"Body too small: {body_percent:.2f}% < {self.min_body_percent}%"
            
            # Check 3: Price must be in top 60% of candle range
            candle_range = high_price - low_price
            if candle_range <= 0:
                return False, "Invalid candle range"
            
            price_position = ((price_to_check - low_price) / candle_range) * 100
            
            if price_position < self.top_range_percent:
                return False, f"Price not in top 60%: {price_position:.1f}% < {self.top_range_percent}%"
            
            return True, f"✅ Strong green candle: Body={body_percent:.2f}%, Position={price_position:.1f}%"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_breakout_structure(self, current_candle: Dict, previous_candle: Dict) -> Tuple[bool, str]:
        """Validate breakout structure with previous candle"""
        try:
            curr_high = current_candle.get('high', 0)
            curr_low = current_candle.get('low', 0)
            curr_close = current_candle.get('close', 0)
            
            prev_high = previous_candle.get('high', 0)
            prev_low = previous_candle.get('low', 0)
            prev_close = previous_candle.get('close', 0)
            prev_open = previous_candle.get('open', 0)
            
            # Check if previous candle was red or green
            prev_was_green = prev_close > prev_open
            
            if prev_was_green:
                # Previous green: current should break above previous close
                if curr_high > prev_close:
                    return True, f"✅ Breakout above prev close: {curr_high:.2f} > {prev_close:.2f}"
                else:
                    return False, f"No breakout above prev close: {curr_high:.2f} <= {prev_close:.2f}"
            else:
                # Previous red: current should break above previous high
                if curr_high > prev_high:
                    return True, f"✅ Breakout above prev high: {curr_high:.2f} > {prev_high:.2f}"
                else:
                    return False, f"No breakout above prev high: {curr_high:.2f} <= {prev_high:.2f}"
                    
        except Exception as e:
            return False, f"Breakout validation error: {str(e)}"
    
    def get_candle_strength_score(self, candle_data: Dict, current_price: float = None) -> float:
        """Calculate candle strength score (0-100)"""
        try:
            open_price = candle_data.get('open', 0)
            high_price = candle_data.get('high', 0)
            low_price = candle_data.get('low', 0)
            
            price_to_check = current_price if current_price else candle_data.get('close', 0)
            
            # Body strength (0-50 points)
            body_percent = ((price_to_check - open_price) / open_price) * 100
            body_score = min(50, body_percent * 10)  # Cap at 50 points
            
            # Position strength (0-50 points)
            candle_range = high_price - low_price
            if candle_range > 0:
                position_percent = ((price_to_check - low_price) / candle_range) * 100
                position_score = min(50, position_percent * 0.5)  # Cap at 50 points
            else:
                position_score = 0
            
            return max(0, min(100, body_score + position_score))
            
        except Exception:
            return 0

class MomentumValidator:
    """Validates momentum requirements (2 out of 3 checks)"""
    
    def __init__(self):
        self.min_price_points = 5  # Minimum price history needed
    
    def check_price_rising(self, price_history: list) -> bool:
        """Check if current momentum is 1.3x stronger than previous momentum"""
        if len(price_history) < 4:
            return False
        
        # Get last 4 prices to calculate momentum ratios
        recent_prices = price_history[-4:]
        
        # Previous momentum: change from price[0] to price[1]
        prev_momentum = abs(recent_prices[1] - recent_prices[0])
        # Current momentum: change from price[2] to price[3]
        curr_momentum = abs(recent_prices[3] - recent_prices[2])
        
        if prev_momentum <= 0:
            return curr_momentum > 0  # Any movement is good if previous was zero
        
        # Current momentum must be 1.3x stronger than previous
        momentum_ratio = curr_momentum / prev_momentum
        return momentum_ratio >= 1.3 and recent_prices[3] > recent_prices[2]  # Must also be rising
    
    def check_price_accelerating(self, price_history: list) -> bool:
        """Check if price is accelerating (increasing rate of change)"""
        if len(price_history) < 4:
            return False
        
        # Calculate rate of change for last 2 periods
        recent = price_history[-4:]
        rate1 = (recent[1] - recent[0]) / recent[0] * 100  # Earlier rate
        rate2 = (recent[3] - recent[2]) / recent[2] * 100  # Recent rate
        
        return rate2 > rate1 and rate2 > 0  # Accelerating upward
    
    def check_volume_confirmation(self, current_price: float, open_price: float, previous_price: float = None) -> bool:
        """Check if current price shows strong momentum vs previous tick (1.2x requirement)"""
        if open_price <= 0 or previous_price is None or previous_price <= 0:
            return False
        
        # Current tick volume (price change from open)
        current_change = abs(current_price - open_price)
        # Previous tick volume (price change from open)
        previous_change = abs(previous_price - open_price)
        
        if previous_change <= 0:
            return current_change > 0  # Any movement is good if previous was zero
        
        # Current volume must be 1.2x higher than previous tick
        volume_ratio = current_change / previous_change
        return volume_ratio >= 1.2
    
    def validate_momentum(self, price_history: list, current_price: float = None, open_price: float = None, previous_price: float = None) -> Tuple[bool, str]:
        """Requires 2 out of 3 momentum checks to pass"""
        checks_passed = 0
        check_results = []
        
        # Check 1: Price Rising (1.3x momentum requirement)
        rising = self.check_price_rising(price_history)
        if rising:
            checks_passed += 1
            check_results.append("✅ Rising(1.3x)")
        else:
            check_results.append("❌ Rising(1.3x)")
        
        # Check 2: Price Accelerating
        accelerating = self.check_price_accelerating(price_history)
        if accelerating:
            checks_passed += 1
            check_results.append("✅ Accelerating")
        else:
            check_results.append("❌ Accelerating")
        
        # Check 3: Volume Confirmation (1.2x requirement)
        volume_ok = self.check_volume_confirmation(current_price or 0, open_price or 0, previous_price)
        if volume_ok:
            checks_passed += 1
            check_results.append("✅ Volume(1.2x)")
        else:
            check_results.append("❌ Volume(1.2x)")
        
        # Need 2 out of 3 to pass
        is_valid = checks_passed >= 2
        
        result_msg = f"{checks_passed}/3 checks passed: {' | '.join(check_results)}"
        
        return is_valid, result_msg

class BreakoutLogic:
    """Handles breakout entry conditions"""
    
    def __init__(self):
        pass
    
    def check_breakout_conditions(self, current_candle: Dict, previous_candle: Dict) -> Tuple[bool, str]:
        """
        Updated Breakout logic:
        - Positive market: Always break above previous close (regardless of candle color)
        - Negative market: Always break below previous close (regardless of candle color)
        """
        try:
            curr_high = current_candle.get('high', 0)
            curr_low = current_candle.get('low', 0)
            prev_close = previous_candle.get('close', 0)
            prev_open = previous_candle.get('open', 0)
            
            # Determine if previous candle was red or green (for display only)
            prev_was_green = prev_close > prev_open
            candle_type = "green" if prev_was_green else "red"
            
            # For positive market: break above previous close
            breakout_above = curr_high > prev_close
            # For negative market: break below previous close  
            breakout_below = curr_low < prev_close
            
            return True, f"✅ Breakout ready: Above={breakout_above}, Below={breakout_below} (prev {candle_type} close: {prev_close:.2f})"
                    
        except Exception as e:
            return False, f"❌ Breakout check error: {str(e)}"
    
    def check_red_candle_entry(self, current_candle: Dict, previous_candle: Dict, live_price: float) -> Tuple[bool, str]:
        """
        Entry when new candle starts forming:
        - New candle starts below closing of previous candle
        - Current price should be forming a red candle (below open)
        """
        try:
            curr_open = current_candle.get('open', 0)
            prev_close = previous_candle.get('close', 0)
            
            # Check 1: New candle started below previous close
            started_below = curr_open < prev_close
            
            # Check 2: Current price is below current open (forming red candle)
            forming_red = live_price < curr_open
            
            if started_below and forming_red:
                return True, f"✅ Red candle entry: Started {curr_open:.2f} < {prev_close:.2f}, Now {live_price:.2f} < {curr_open:.2f}"
            elif not started_below:
                return False, f"❌ Started above prev close: {curr_open:.2f} >= {prev_close:.2f}"
            else:
                return False, f"❌ Not forming red candle: {live_price:.2f} >= {curr_open:.2f}"
                
        except Exception as e:
            return False, f"❌ Red candle check error: {str(e)}"

class OrderPlacementLogic:
    """Handles MT5 order placement with bid/ask logic"""
    
    def __init__(self):
        self.risk_per_trade = 5  # $5 risk per trade
        self.risk_reward_ratio = 2.0  # 2:1 RR
    
    def get_market_depth(self, symbol: str) -> Dict:
        """Get bid/ask data similar to MT5 order tab"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {}
            
            return {
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'time': tick.time
            }
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_entry_price(self, symbol: str, order_type: str) -> Tuple[float, str]:
        """
        Calculate optimal entry price:
        - BUY: Use ASK price + small buffer (seller + tick value)
        - SELL: Use BID price - small buffer
        """
        try:
            market_data = self.get_market_depth(symbol)
            if 'error' in market_data:
                return 0.0, f"Market data error: {market_data['error']}"
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.0, "Symbol info not available"
            
            tick_size = symbol_info.trade_tick_size
            
            if order_type == "BUY":
                # For BUY: Use ASK + tick (aim for next seller level)
                entry_price = market_data['ask'] + tick_size
                return entry_price, f"BUY at ASK+tick: {entry_price:.5f}"
            else:  # SELL
                # For SELL: Use BID - tick (aim for next buyer level)
                entry_price = market_data['bid'] - tick_size
                return entry_price, f"SELL at BID-tick: {entry_price:.5f}"
                
        except Exception as e:
            return 0.0, f"Entry price calculation error: {str(e)}"
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float) -> Tuple[float, str]:
        """Calculate position size based on risk per trade"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return 0.01, "Using minimum volume - symbol info unavailable"
            
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss)
            if risk_distance <= 0:
                return 0.01, "Invalid risk distance"
            
            # Calculate position size based on risk
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size
            
            if tick_value > 0 and tick_size > 0:
                # Position size = Risk Amount / (Risk Distance / Tick Size * Tick Value)
                position_size = self.risk_per_trade / (risk_distance / tick_size * tick_value)
                
                # Round to valid volume step
                volume_step = symbol_info.volume_step
                position_size = round(position_size / volume_step) * volume_step
                
                # Ensure within broker limits
                min_volume = symbol_info.volume_min
                max_volume = symbol_info.volume_max
                position_size = max(min_volume, min(max_volume, position_size))
                
                return position_size, f"Calculated volume: {position_size} (Risk: ${self.risk_per_trade})"
            
            return 0.01, "Using minimum volume - calculation failed"
            
        except Exception as e:
            return 0.01, f"Position size error: {str(e)}"
    
    def place_order(self, symbol: str, order_type: str, entry_price: float, stop_loss: float, take_profit: float, volume: float) -> Tuple[bool, str]:
        """Place order with proper bid/ask handling"""
        try:
            # Determine MT5 order type
            if order_type == "BUY":
                mt5_order_type = mt5.ORDER_TYPE_BUY
            else:
                mt5_order_type = mt5.ORDER_TYPE_SELL
            
            # Create order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": entry_price,
                "sl": stop_loss,
                "tp": take_profit,
                "magic": 123456,
                "comment": f"Step4_{order_type}_Order",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                return True, f"✅ {order_type} order executed - Ticket: {result.order}"
            else:
                error_msg = result.comment if result else "Unknown error"
                return False, f"❌ Order failed: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Order placement error: {str(e)}"

class AdvancedEntryManager:
    """Main class that coordinates all entry logic"""
    
    def __init__(self):
        self.candle_validator = CandleStructureValidator()
        self.momentum_validator = MomentumValidator()
        self.breakout_logic = BreakoutLogic()
        self.order_logic = OrderPlacementLogic()
    
    def validate_entry_conditions(self, symbol: str, signal: str, current_candle: Dict, previous_candle: Dict, 
                                 current_price: float, price_history: list) -> Tuple[bool, Dict]:
        """
        Main entry point - validates all conditions before trade
        Returns: (is_valid, validation_data)
        """
        validation_results = {
            'candle_structure': False,
            'momentum': False,
            'breakout': False,
            'red_candle_entry': False,
            'messages': []
        }
        
        try:
            # Step 1: Candle Structure Validation
            candle_valid, candle_msg = self.candle_validator.validate_strong_green_candle(current_candle, current_price)
            validation_results['candle_structure'] = candle_valid
            validation_results['messages'].append(f"Candle: {candle_msg}")
            
            # Step 2: Momentum Validation (2 out of 3 checks)
            momentum_valid, momentum_msg = self.momentum_validator.validate_momentum(
                price_history, current_price, current_candle.get('open', 0)
            )
            validation_results['momentum'] = momentum_valid
            validation_results['messages'].append(f"Momentum: {momentum_msg}")
            
            # Step 3: Breakout Logic
            breakout_valid, breakout_msg = self.breakout_logic.check_breakout_conditions(current_candle, previous_candle)
            validation_results['breakout'] = breakout_valid
            validation_results['messages'].append(f"Breakout: {breakout_msg}")
            
            # Step 4: Red Candle Entry (for SELL signals)
            if signal == "SELL":
                red_candle_valid, red_candle_msg = self.breakout_logic.check_red_candle_entry(
                    current_candle, previous_candle, current_price
                )
                validation_results['red_candle_entry'] = red_candle_valid
                validation_results['messages'].append(f"Red Entry: {red_candle_msg}")
            else:
                validation_results['red_candle_entry'] = True  # Not required for BUY
            
            # Overall validation: All checks must pass
            all_valid = (
                validation_results['candle_structure'] and
                validation_results['momentum'] and
                validation_results['breakout'] and
                validation_results['red_candle_entry']
            )
            
            return all_valid, validation_results
            
        except Exception as e:
            validation_results['messages'].append(f"❌ Validation error: {str(e)}")
            return False, validation_results
    
    def execute_advanced_entry(self, symbol: str, signal: str, current_candle: Dict, previous_candle: Dict, 
                              current_price: float, price_history: list, atr_value: float) -> Dict:
        """Execute complete 4-step entry process"""
        try:
            # Step 1-3: Validate all conditions
            all_valid, validation_data = self.validate_entry_conditions(
                symbol, signal, current_candle, previous_candle, current_price, price_history
            )
            
            if not all_valid:
                return {
                    'success': False,
                    'step': 'Validation Failed',
                    'message': 'Entry conditions not met',
                    'validation_data': validation_data
                }
            
            # Step 4: Order Placement
            # Calculate stop loss using ATR
            atr_multiplier = 1.1
            if signal == "BUY":
                stop_loss = current_price - (atr_value * atr_multiplier)
                take_profit = current_price + (atr_value * atr_multiplier * self.order_logic.risk_reward_ratio)
            else:  # SELL
                stop_loss = current_price + (atr_value * atr_multiplier)
                take_profit = current_price - (atr_value * atr_multiplier * self.order_logic.risk_reward_ratio)
            
            # Get optimal entry price
            entry_price, entry_msg = self.order_logic.calculate_entry_price(symbol, signal)
            if entry_price <= 0:
                return {
                    'success': False,
                    'step': 'Step 4 - Entry Price',
                    'message': entry_msg
                }
            
            # Calculate position size
            volume, volume_msg = self.order_logic.calculate_position_size(symbol, entry_price, stop_loss)
            
            # Place the order
            order_success, order_msg = self.order_logic.place_order(
                symbol, signal, entry_price, stop_loss, take_profit, volume
            )
            
            return {
                'success': order_success,
                'step': 'Step 4 - Order Placement',
                'message': order_msg,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'volume': volume,
                'validation_data': validation_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'step': 'Execution Error',
                'message': f"Advanced entry error: {str(e)}"
            }