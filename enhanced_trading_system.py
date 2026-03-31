import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import time
from datetime import datetime
import talib

class EnhancedTradingSystem:
    def __init__(self, symbol="EURUSD", risk_amount=20):
        self.symbol = symbol
        self.risk_amount = risk_amount
        self.min_balance_threshold = risk_amount
        self.trend_highest_price = 0.0          # Highest price in current bullish trend
        self.trend_lowest_price = 999999.0      # Lowest price in current bearish trend
        self.supertrend_stop_loss = {}          # SuperTrend stop loss per position
        self.partial_exit_taken = {}
        self.trend_high = {}
        self.trend_low = {}

    def connect_mt5(self):
        """Initialize MT5 connection"""
        if not mt5.initialize():
            print("MT5 initialization failed")
            return False
        
        # Login credentials
        login = 213711922
        password = "j6t#UeuH"
        server = "OctaFX-Demo"
        
        if not mt5.login(login, password, server):
            print(f"Login failed: {mt5.last_error()}")
            return False
        
        print(f"Connected to MT5: {mt5.account_info().name}")
        return True
    
    def get_market_data(self, timeframe=mt5.TIMEFRAME_M5, count=100):
        """Get market data for analysis"""
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def calculate_supertrend(self, df, period=5, multiplier=0.7):
        """Calculate Supertrend indicator"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calculate ATR
        atr = talib.ATR(high, low, close, timeperiod=period)
        
        # Calculate basic bands
        hl2 = (high + low) / 2
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # Initialize arrays
        supertrend = np.zeros(len(close))
        direction = np.ones(len(close))  # 1 for uptrend, -1 for downtrend
        
        for i in range(1, len(close)):
            # Upper band calculation
            if upper_band[i] < upper_band[i-1] or close[i-1] > upper_band[i-1]:
                upper_band[i] = upper_band[i]
            else:
                upper_band[i] = upper_band[i-1]
            
            # Lower band calculation
            if lower_band[i] > lower_band[i-1] or close[i-1] < lower_band[i-1]:
                lower_band[i] = lower_band[i]
            else:
                lower_band[i] = lower_band[i-1]
            
            # Supertrend calculation
            if close[i] <= lower_band[i]:
                supertrend[i] = lower_band[i]
                direction[i] = -1
            elif close[i] >= upper_band[i]:
                supertrend[i] = upper_band[i]
                direction[i] = 1
            else:
                supertrend[i] = supertrend[i-1]
                direction[i] = direction[i-1]
        
        return supertrend, direction
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # RSI
        rsi = talib.RSI(close, timeperiod=14)

        # ATR for stop loss (period=10)
        atr = talib.ATR(high, low, close, timeperiod=10)
        
        # Supertrend
        supertrend, st_direction = self.calculate_supertrend(df, period=10, multiplier=0.9)
        
        return {
            'rsi': rsi[-1] if len(rsi) > 0 else 0,
            'atr': atr[-1] if len(atr) > 0 else 0,
            'supertrend_direction': st_direction[-1] if len(st_direction) > 0 else 0,
            'supertrend_value': supertrend[-1] if len(supertrend) > 0 else 0
        }
    
    def check_account_balance(self):
        """Check account balance and determine available risk"""
        account_info = mt5.account_info()
        if account_info is None:
            return 0
        
        balance = account_info.balance
        equity = account_info.equity
        
        # Use the lower of balance or equity
        available_balance = min(balance, equity)
        
        # Return the minimum of risk_amount or available balance
        return min(self.risk_amount, available_balance)
    
    def step1_signal_generation(self, indicators, current_candle, previous_candle):
        """STEP 1: Enhanced signal generation with Supertrend and candle color"""
        rsi = indicators['rsi']
        st_direction = indicators['supertrend_direction']
        
        current_price = current_candle['close']
        current_open = current_candle['open']
        
        # Determine current candle color
        is_green_candle = current_price > current_open
        is_red_candle = current_price < current_open
        
        # BUY Signal: RSI > 30, Supertrend = 1, Green Candle
        buy_conditions = (
            rsi > 30 and
            st_direction == 1 and
            is_green_candle
        )
        
        # SELL Signal: RSI < 70, Supertrend = 1, Red Candle
        sell_conditions = (
            rsi < 70 and
            st_direction == -1 and
            is_red_candle
        )
        
        signal = "NONE"
        if buy_conditions:
            signal = "BUY"
        elif sell_conditions:
            signal = "SELL"
        
        return {
            'signal': signal,
            'rsi': rsi,
            'supertrend_direction': st_direction,
            'candle_color': 'GREEN' if is_green_candle else 'RED' if is_red_candle else 'DOJI',
            'conditions_met': buy_conditions or sell_conditions
        }
    
    def step2_entry_logic(self, current_candle, previous_candle, signal):
        """STEP 2: Enhanced candle structure validation"""
        current_price = current_candle['close']
        current_open = current_candle['open']
        prev_close = previous_candle['close']
        prev_open = previous_candle['open']
        
        # Strong candle validation
        is_strong_green = current_price > current_open
        body_size = abs(current_price - current_open)
        body_percentage = (body_size / current_price) * 100
        
        # Minimum body requirement: 0.01%
        min_body_valid = body_percentage >= 0.01
        
        # Breakout logic
        breakout_valid = False
        breakout_msg = ""
        
        if signal == "BUY":  # Positive market
            # Break above previous close regardless of previous candle color
            if current_price > prev_close:
                breakout_valid = True
                breakout_msg = f"BUY breakout: {current_price:.5f} > {prev_close:.5f}"
            else:
                breakout_msg = f"No BUY breakout: {current_price:.5f} <= {prev_close:.5f}"
                
        elif signal == "SELL":  # Negative market
            # Break below previous close regardless of previous candle color
            if current_price < prev_close:
                breakout_valid = True
                breakout_msg = f"SELL breakout: {current_price:.5f} < {prev_close:.5f}"
            else:
                breakout_msg = f"No SELL breakout: {current_price:.5f} >= {prev_close:.5f}"
        
        candle_valid = is_strong_green and min_body_valid
        step2_valid = candle_valid and breakout_valid
        
        return {
            'valid': step2_valid,
            'candle_valid': candle_valid,
            'breakout_valid': breakout_valid,
            'body_percentage': body_percentage,
            'breakout_msg': breakout_msg,
            'candle_msg': f"Body: {body_percentage:.3f}% ({'PASS' if min_body_valid else 'FAIL'})"
        }
    
    def step3_enter_trading(self, df, signal):
        """STEP 3: Enhanced momentum/volume/acceleration validation"""
        if len(df) < 10:
            return {'valid': True, 'volume_valid': True, 'acceleration_valid': True, 'momentum_valid': True, 'checks_passed': 3}
        
        # Get recent data
        recent_volumes = df['tick_volume'].tail(5).values
        recent_closes = df['close'].tail(10).values
        
        # Volume validation (tick volume trend)
        volume_trend = np.mean(recent_volumes[-3:]) > np.mean(recent_volumes[-5:-2])
        volume_valid = volume_trend
        
        # Acceleration validation (price acceleration)
        if len(recent_closes) >= 5:
            recent_change = abs(recent_closes[-1] - recent_closes[-3])
            earlier_change = abs(recent_closes[-3] - recent_closes[-5])
            acceleration_valid = recent_change > earlier_change
        else:
            acceleration_valid = True
        
        # Momentum validation (directional momentum)
        if len(recent_closes) >= 3:
            momentum = recent_closes[-1] - recent_closes[-3]
            if signal == "BUY":
                momentum_valid = momentum > 0
            elif signal == "SELL":
                momentum_valid = momentum < 0
            else:
                momentum_valid = True
        else:
            momentum_valid = True
        
        # Check for new red candle condition
        current_candle = df.iloc[-1]
        previous_candle = df.iloc[-2] if len(df) > 1 else current_candle
        
        new_red_candle = (current_candle['close'] < current_candle['open'] and 
                         current_candle['close'] < previous_candle['close'])
        
        # Count passed checks
        checks = [volume_valid, acceleration_valid, momentum_valid]
        checks_passed = sum(checks)
        
        # Need 2 out of 3 + new red candle condition
        step3_valid = checks_passed >= 2 and new_red_candle
        
        return {
            'valid': step3_valid,
            'volume_valid': volume_valid,
            'acceleration_valid': acceleration_valid,
            'momentum_valid': momentum_valid,
            'new_red_candle': new_red_candle,
            'checks_passed': checks_passed
        }
    
    def step4_order_placement(self, signal, current_price, atr_value):
        """STEP 4: Enhanced order placement with account balance check"""
        # Check account balance
        available_risk = self.check_account_balance()
        if available_risk < self.min_balance_threshold:
            return {
                'valid': False,
                'error': f"Insufficient balance: ${available_risk:.2f} < ${self.min_balance_threshold}"
            }
        
        # Get market data
        tick = mt5.symbol_info_tick(self.symbol)
        symbol_info = mt5.symbol_info(self.symbol)
        
        if not tick or not symbol_info:
            return {'valid': False, 'error': 'Market data unavailable'}
        
        # Enhanced pricing strategy
        tick_size = symbol_info.trade_tick_size
        
        if signal == "BUY":
            entry_price = tick.ask
            stop_loss = 0
            take_profit = 0 # 1.2 RR
        elif signal == "SELL":
            entry_price = tick.bid 
            stop_loss = 0
            take_profit = 0
        else:
            return {'valid': False, 'error': 'No valid signal'}
        
        # Volume = Account Balance / (Current Price * Contract Size)
        account_info = mt5.account_info()
        account_balance = account_info.balance if account_info else 1000.0
        contract_size = symbol_info.trade_contract_size
        raw_volume = account_balance / (entry_price * contract_size)

        # Validate against broker limits
        min_vol = symbol_info.volume_min
        max_vol = symbol_info.volume_max
        volume_step = symbol_info.volume_step

        volume = max(min_vol, round(raw_volume / volume_step) * volume_step)
        volume = min(volume, max_vol)

        
        return {
            'valid': True,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'volume': volume,
            'available_risk': available_risk,
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': tick.ask - tick.bid
        }
    
    def execute_trade(self, signal, order_data):
        """Execute the trade"""
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': self.symbol,
            'volume': order_data['volume'],
            'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
            'price': order_data['entry_price'],
            'sl': order_data['stop_loss'],
            'tp': order_data['take_profit'],
            'comment': 'Enhanced 4-Step System',
            'type_filling': mt5.ORDER_FILLING_IOC,
            'magic': 234567
        }
        
        result = mt5.order_send(request)
        return result
    
    def manage_positions(self):
        """Monitor and manage open positions with dynamic exits"""
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            return
        
        df = self.get_market_data()
        if df is None or len(df) < 10:
            return
        
        indicators = self.calculate_indicators(df)
        current_candle = df.iloc[-1]
        previous_candle = df.iloc[-2]
        
        current_price = current_candle['close']
        prev_close = previous_candle['close']
        prev_open = previous_candle['open']
        st_direction = indicators['supertrend_direction']
        
        for pos in positions:
            pos_ticket = pos.ticket
            pos_type = "BUY" if pos.type == 0 else "SELL"
            entry_price = pos.price_open
            profit = pos.profit
            
            # Initialize trend tracking
            if pos_ticket not in self.trend_high:
                self.trend_high[pos_ticket] = entry_price
            if pos_ticket not in self.trend_low:
                self.trend_low[pos_ticket] = entry_price
            
            # Update trend extremes
            if pos_type == "BUY":
                self.trend_high[pos_ticket] = max(self.trend_high[pos_ticket], current_price)
            else:
                self.trend_low[pos_ticket] = min(self.trend_low[pos_ticket], current_price)
            
            # PARTIAL EXIT: $4 movement
            if pos_ticket not in self.partial_exit_taken:
                price_movement = abs(current_price - entry_price)
                if price_movement >= 4.0:
                    half_volume = round(pos.volume / 2, 2)
                    if half_volume >= 0.01:
                        tick = mt5.symbol_info_tick(self.symbol)
                        close_type = mt5.ORDER_TYPE_SELL if pos_type == "BUY" else mt5.ORDER_TYPE_BUY
                        close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
                        
                        request = {
                            'action': mt5.TRADE_ACTION_DEAL,
                            'symbol': self.symbol,
                            'volume': half_volume,
                            'type': close_type,
                            'position': pos_ticket,
                            'price': close_price,
                            'magic': 234567,
                            'comment': 'Partial Exit',
                            'type_filling': mt5.ORDER_FILLING_IOC,
                        }
                        
                        result = mt5.order_send(request)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            self.partial_exit_taken[pos_ticket] = True
                            print(f"\n[PARTIAL] #{pos_ticket} | 50% closed at ${price_movement:.2f}")
                            continue
            
            # FULL EXIT CONDITIONS
            exit_signal = False
            exit_reason = ""
            
            # 1. Supertrend Reversal
            if pos_type == "BUY" and st_direction == -1:
                exit_signal = True
                exit_reason = "ST Reversal"
            elif pos_type == "SELL" and st_direction == 1:
                exit_signal = True
                exit_reason = "ST Reversal"
            
            # 2. Candle Closed with opposite color
            if not exit_signal:
                is_red = prev_close < prev_open
                is_green = prev_close > prev_open
                
                if pos_type == "BUY" and is_red:
                    exit_signal = True
                    exit_reason = "Red Candle Closed"
                elif pos_type == "SELL" and is_green:
                    exit_signal = True
                    exit_reason = "Green Candle Closed"
            
            # 3. Price below/above trend extreme
            if not exit_signal:
                if pos_type == "BUY" and current_price < self.trend_high[pos_ticket]:
                    exit_signal = True
                    exit_reason = f"Below High {self.trend_high[pos_ticket]:.2f}"
                elif pos_type == "SELL" and current_price > self.trend_low[pos_ticket]:
                    exit_signal = True
                    exit_reason = f"Above Low {self.trend_low[pos_ticket]:.2f}"
            
            # Execute exit
            if exit_signal:
                tick = mt5.symbol_info_tick(self.symbol)
                close_type = mt5.ORDER_TYPE_SELL if pos_type == "BUY" else mt5.ORDER_TYPE_BUY
                close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
                
                request = {
                    'action': mt5.TRADE_ACTION_DEAL,
                    'symbol': self.symbol,
                    'volume': pos.volume,
                    'type': close_type,
                    'position': pos_ticket,
                    'price': close_price,
                    'magic': 234567,
                    'comment': exit_reason,
                    'type_filling': mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"\n[EXIT] #{pos_ticket} | {exit_reason} | P/L: ${profit:.2f}")
                    self.partial_exit_taken.pop(pos_ticket, None)
                    self.trend_high.pop(pos_ticket, None)
                    self.trend_low.pop(pos_ticket, None)

    
    def run_analysis(self):
        """Main trading loop"""
        if not self.connect_mt5():
            return
        
        print("ENHANCED TRADING SYSTEM - LIVE ANALYSIS")
        print("=" * 60)
        print(f"Symbol: {self.symbol} | Risk: ${self.risk_amount}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                # Get market data
                df = self.get_market_data()
                if df is None or len(df) < 50:
                    print("Insufficient market data")
                    time.sleep(5)
                    continue
                
                # Calculate indicators
                indicators = self.calculate_indicators(df)
                current_candle = df.iloc[-1].to_dict()
                previous_candle = df.iloc[-2].to_dict() if len(df) > 1 else current_candle
                
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ANALYSIS")
                print("=" * 50)
                
                # STEP 1: Signal Generation
                step1_result = self.step1_signal_generation(indicators, current_candle, previous_candle)
                print(f"STEP 1 -> SIGNAL: {step1_result['signal']}")
                print(f"  RSI: {step1_result['rsi']:.1f}")
                print(f"  Supertrend: {step1_result['supertrend_direction']} | Candle: {step1_result['candle_color']}")
                print(f"  Conditions: {'PASS' if step1_result['conditions_met'] else 'FAIL'}")
                
                if not step1_result['conditions_met']:
                    print("  -> Waiting for signal conditions...")
                    time.sleep(5)
                    continue
                
                signal = step1_result['signal']
                
                # STEP 4: Order Placement
                step4_result = self.step4_order_placement(signal, current_candle['close'], indicators['atr'])
                print(f"\nSTEP 4 -> ORDER PLACEMENT: {'PASS' if step4_result['valid'] else 'FAIL'}")
                
                if step4_result['valid']:
                    print(f"  Entry: {step4_result['entry_price']:.5f} | SL: {step4_result['stop_loss']:.5f} | TP: {step4_result['take_profit']:.5f}")
                    print(f"  Volume: {step4_result['volume']:.2f} | Risk: ${step4_result['available_risk']:.2f}")
                    print(f"  Bid: {step4_result['bid']:.5f} | Ask: {step4_result['ask']:.5f} | Spread: {step4_result['spread']:.5f}")
                else:
                    print(f"  Error: {step4_result.get('error', 'Unknown')}")
                
                # FINAL DECISION
                all_steps_valid = (step1_result['conditions_met'] and 
                                  step4_result['valid'])
                
                print(f"\nFINAL DECISION: {'EXECUTE' if all_steps_valid else 'WAIT'}")
                
                if all_steps_valid:
                    print(f"  [OK] EXECUTING {signal} TRADE - ALL 4 STEPS VALIDATED!")
                    
                    # Execute trade
                    result = self.execute_trade(signal, step4_result)
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"  [SUCCESS] TRADE EXECUTED: Ticket #{result.order} at {result.price:.5f}")
                    else:
                        error_msg = result.comment if result else "Unknown error"
                        print(f"  [FAILED] TRADE ERROR: {error_msg}")
                else:
                    print(f"  -> Waiting: Step1={step1_result['conditions_met']} | "
                          f"Step4={step4_result['valid']}")

                # Manage open positions (outside the if block)
                self.manage_positions()

                time.sleep(5)  # Wait 5 seconds between analyses
                
        except KeyboardInterrupt:
            print("\n\nTrading system stopped by user")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    # Initialize and run the enhanced trading system
    trading_system = EnhancedTradingSystem(symbol="EURUSD", risk_amount=20)
    trading_system.run_analysis()