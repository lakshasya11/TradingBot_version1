import MetaTrader5 as mt5
import numpy as np
import pandas as pd
import time
from datetime import datetime

class EnhancedTradingSystem:
    def __init__(self, symbol="EURUSD", risk_amount=20):
        self.symbol = symbol
        self.risk_amount = risk_amount
        self.min_balance_threshold = risk_amount
        
    def connect_mt5(self):
        """Initialize MT5 connection"""
        if not mt5.initialize():
            print("MT5 initialization failed")
            return False
        
        # Login credentials from .env
        login = 5044214016
        password = "Tq-w6rPx"
        server = "MetaQuotes-Demo"
        
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
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI manually"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_ema(self, prices, period):
        """Calculate EMA manually"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def calculate_atr(self, high, low, close, period=10):
        """Calculate ATR manually"""
        if len(high) < period + 1:
            return np.mean(high) - np.mean(low)
        
        tr_list = []
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr_list.append(max(tr1, tr2, tr3))
        
        return np.mean(tr_list[-period:])
    
    def calculate_supertrend(self, df, period=5, multiplier=0.7):
        """Calculate Supertrend indicator manually"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        if len(high) < period + 1:
            return 0, 1
        
        # Calculate ATR for Supertrend
        atr = self.calculate_atr(high, low, close, period)
        
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
        
        return supertrend[-1], direction[-1]
    
    def calculate_indicators(self, df):
        """Calculate all technical indicators"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # RSI
        rsi = self.calculate_rsi(close, 14)
        
        # EMA
        ema9 = self.calculate_ema(close, 9)
        ema21 = self.calculate_ema(close, 21)
        
        # ATR for stop loss (period=10)
        atr = self.calculate_atr(high, low, close, 10)
        
        # Supertrend
        supertrend_value, st_direction = self.calculate_supertrend(df, period=5, multiplier=0.7)
        
        return {
            'rsi': rsi,
            'ema9': ema9,
            'ema21': ema21,
            'atr': atr,
            'supertrend_direction': st_direction,
            'supertrend_value': supertrend_value
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
        ema9 = indicators['ema9']
        ema21 = indicators['ema21']
        st_direction = indicators['supertrend_direction']
        
        current_price = current_candle['close']
        current_open = current_candle['open']
        
        # Determine current candle color
        is_green_candle = current_price > current_open
        is_red_candle = current_price < current_open
        
        # BUY Signal: RSI > 45, EMA9 > EMA21, Supertrend = 1, Green Candle
        buy_conditions = (
            rsi > 45 and
            ema9 > ema21 and
            st_direction == 1 and
            is_green_candle
        )
        
        # SELL Signal: RSI < 55, EMA9 < EMA21, Supertrend = 1, Red Candle
        sell_conditions = (
            rsi < 55 and
            ema9 < ema21 and
            st_direction == 1 and
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
            'ema9': ema9,
            'ema21': ema21,
            'supertrend_direction': st_direction,
            'candle_color': 'GREEN' if is_green_candle else 'RED' if is_red_candle else 'DOJI',
            'conditions_met': buy_conditions or sell_conditions
        }
    
    def step2_entry_logic(self, current_candle, previous_candle, signal):
        """STEP 2: Enhanced candle structure validation"""
        current_price = current_candle['close']
        current_open = current_candle['open']
        prev_close = previous_candle['close']
        
        # Strong candle validation
        is_strong_green = current_price > current_open
        body_size = abs(current_price - current_open)
        body_percentage = (body_size / current_price) * 100
        
        # Minimum body requirement: 0.05%
        min_body_valid = body_percentage >= 0.05
        
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
            return {'valid': True, 'volume_valid': True, 'acceleration_valid': True, 'momentum_valid': True, 'checks_passed': 3, 'new_red_candle': True}
        
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
            # ASK + tick for better fill probability
            entry_price = tick.ask + tick_size
            stop_loss = entry_price - (atr_value * 1.2)  # ATR * 1.2
            take_profit = entry_price + (abs(entry_price - stop_loss) * 1.2)  # 1.2 RR
        elif signal == "SELL":
            # BID - tick for better fill probability
            entry_price = tick.bid - tick_size
            stop_loss = entry_price + (atr_value * 1.2)  # ATR * 1.2
            take_profit = entry_price - (abs(stop_loss - entry_price) * 1.2)  # 1.2 RR
        else:
            return {'valid': False, 'error': 'No valid signal'}
        
        # Calculate position size based on available risk
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance > 0:
            # Calculate lot size based on available risk
            point_value = symbol_info.trade_contract_size * symbol_info.point
            risk_per_point = available_risk / (stop_distance / symbol_info.point)
            raw_volume = risk_per_point / point_value
            
            # Validate against broker limits
            min_vol = symbol_info.volume_min
            max_vol = symbol_info.volume_max
            volume_step = symbol_info.volume_step
            
            volume = max(min_vol, round(raw_volume / volume_step) * volume_step)
            volume = min(volume, max_vol)
        else:
            volume = symbol_info.volume_min
        
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
                print(f"  RSI: {step1_result['rsi']:.1f} | EMA9: {step1_result['ema9']:.5f} | EMA21: {step1_result['ema21']:.5f}")
                print(f"  Supertrend: {step1_result['supertrend_direction']} | Candle: {step1_result['candle_color']}")
                print(f"  Conditions: {'PASS' if step1_result['conditions_met'] else 'FAIL'}")
                
                if not step1_result['conditions_met']:
                    print("  -> Waiting for signal conditions...")
                    time.sleep(5)
                    continue
                
                signal = step1_result['signal']
                
                # STEP 2: Entry Logic
                step2_result = self.step2_entry_logic(current_candle, previous_candle, signal)
                print(f"\nSTEP 2 -> ENTRY LOGIC: {'PASS' if step2_result['valid'] else 'FAIL'}")
                print(f"  {step2_result['candle_msg']}")
                print(f"  {step2_result['breakout_msg']}")
                
                # STEP 3: Enter Trading
                step3_result = self.step3_enter_trading(df, signal)
                print(f"\nSTEP 3 -> ENTER TRADING: {'PASS' if step3_result['valid'] else 'FAIL'}")
                print(f"  Volume: {'PASS' if step3_result['volume_valid'] else 'FAIL'} | "
                      f"Acceleration: {'PASS' if step3_result['acceleration_valid'] else 'FAIL'} | "
                      f"Momentum: {'PASS' if step3_result['momentum_valid'] else 'FAIL'}")
                print(f"  New Red Candle: {'YES' if step3_result['new_red_candle'] else 'NO'}")
                print(f"  Checks Passed: {step3_result['checks_passed']}/3")
                
                # STEP 4: Order Placement
                step4_result = self.step4_order_placement(signal, current_candle['close'], indicators['atr'])
                print(f"\nSTEP 4 -> ORDER PLACEMENT: {'PASS' if step4_result['valid'] else 'FAIL'}")
                
                if step4_result['valid']:
                    print(f"  Entry: {step4_result['entry_price']:.5f} | SL: {step4_result['stop_loss']:.5f} | TP: {step4_result['take_profit']:.5f}")
                    print(f"  Volume: {step4_result['volume']:.2f} | Risk: ${step4_result['available_risk']:.2f} | RR: 1.2:1")
                    print(f"  Bid: {step4_result['bid']:.5f} | Ask: {step4_result['ask']:.5f} | Spread: {step4_result['spread']:.5f}")
                else:
                    print(f"  Error: {step4_result.get('error', 'Unknown')}")
                
                # FINAL DECISION
                all_steps_valid = (step1_result['conditions_met'] and 
                                 step2_result['valid'] and 
                                 step3_result['valid'] and 
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
                          f"Step2={step2_result['valid']} | "
                          f"Step3={step3_result['valid']} | "
                          f"Step4={step4_result['valid']}")
                
                time.sleep(5)  # Wait 5 seconds between analyses
                
        except KeyboardInterrupt:
            print("\n\nTrading system stopped by user")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    # Initialize and run the enhanced trading system
    trading_system = EnhancedTradingSystem(symbol="EURUSD", risk_amount=20)
    trading_system.run_analysis()