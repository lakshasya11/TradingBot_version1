import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator, MomentumValidator, BreakoutLogic, AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy

def market_realistic_trading():
    """Market-Realistic Trading System - Only processes genuine new ticks (2-3/sec)"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    # Initialize components
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    validator = CandleStructureValidator()
    momentum_validator = MomentumValidator()
    breakout_logic = BreakoutLogic()
    entry_manager = AdvancedEntryManager()
    
    # Price history for momentum analysis
    price_history = []
    
    print("MARKET-REALISTIC TRADING SYSTEM")
    print("=" * 60)
    print("Processing ONLY genuine new ticks (2-3 per second)")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Track tick timing
    last_tick_time = 0
    tick_count = 0
    start_time = time.time()
    last_analysis_time = time.time()
    
    try:
        while True:
            # Get live market data
            symbol = "XAUUSD"
            tick = mt5.symbol_info_tick(symbol)
            current_time = time.time()
            
            # ONLY process genuine NEW ticks (market-realistic approach)
            if tick and tick.time > last_tick_time:
                tick_count += 1
                time_since_last = current_time - last_analysis_time
                last_analysis_time = current_time
                last_tick_time = tick.time
                
                # Show tick timing info
                tick_rate = tick_count / (current_time - start_time) if current_time > start_time else 0
                print(f"\n[TICK #{tick_count}] Rate: {tick_rate:.1f}/sec | Gap: {time_since_last:.2f}s")
                
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            
                if rates is not None and len(rates) >= 2:
                    df = pd.DataFrame(rates)
                    
                    # STEP 1: Entry Conditions Analysis
                    analysis = strategy.analyze_timeframe("M1")
                    signal = strategy.check_entry_conditions(analysis)
                    
                    # STEP 2: Candle Structure Validation
                    current_candle = {
                        'open': df.iloc[-1]['open'],
                        'close': df.iloc[-1]['close'],
                        'high': df.iloc[-1]['high'],
                        'low': df.iloc[-1]['low']
                    }
                    
                    previous_candle = {
                        'open': df.iloc[-2]['open'],
                        'close': df.iloc[-2]['close'],
                        'high': df.iloc[-2]['high'],
                        'low': df.iloc[-2]['low']
                    }
                    
                    current_price = tick.bid
                    
                    # Update price history for momentum analysis
                    price_history.append(current_price)
                    if len(price_history) > 10:  # Keep last 10 prices
                        price_history = price_history[-10:]
                    
                    # Validate candle structure
                    is_valid_candle, candle_msg = validator.validate_strong_green_candle(current_candle, current_price)
                    strength_score = validator.get_candle_strength_score(current_candle, current_price)
                    
                    # Breakout logic
                    prev_close = previous_candle['close']
                    market_positive = signal == "BUY" or ('buy_conditions_met' in locals() and buy_conditions_met)
                    market_negative = signal == "SELL" or ('sell_conditions_met' in locals() and sell_conditions_met)
                    
                    if market_positive:
                        breakout_valid = current_price > prev_close
                        breakout_msg = f"Positive market: Price {current_price:.2f} {'above' if breakout_valid else 'below'} prev close {prev_close:.2f}"
                    elif market_negative:
                        breakout_valid = current_price < prev_close
                        breakout_msg = f"Negative market: Price {current_price:.2f} {'below' if breakout_valid else 'above'} prev close {prev_close:.2f}"
                    else:
                        breakout_valid = False
                        breakout_msg = "No clear market direction - waiting for signal"
                    
                    # Step 3: Volume, Acceleration, Momentum validation
                    extended_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
                    extended_df = pd.DataFrame(extended_rates) if extended_rates is not None else df

                    # Volume check
                    current_volume = df.iloc[-1]['tick_volume']
                    avg_volume = extended_df['tick_volume'].tail(5).mean()
                    volume_valid = current_volume > (avg_volume * 1.2)
                    volume_msg = f"Volume: {current_volume} vs Avg: {avg_volume:.0f} ({'PASS' if volume_valid else 'FAIL'})"

                    # Acceleration check
                    if len(price_history) >= 7:
                        try:
                            recent_changes = [price_history[i] - price_history[i-1] for i in range(-3, 0)]
                            earlier_changes = [price_history[i] - price_history[i-1] for i in range(-6, -3)]
                            recent_avg = sum(abs(x) for x in recent_changes) / len(recent_changes)
                            earlier_avg = sum(abs(x) for x in earlier_changes) / len(earlier_changes)
                            acceleration_valid = recent_avg > (earlier_avg * 1.1)
                            acceleration_msg = f"Acceleration: Recent={recent_avg:.3f} vs Earlier={earlier_avg:.3f} ({'PASS' if acceleration_valid else 'FAIL'})"
                        except IndexError:
                            acceleration_valid = True
                            acceleration_msg = "Acceleration: Index error (DEFAULT PASS)"
                    else:
                        acceleration_valid = True
                        acceleration_msg = "Acceleration: Insufficient data (DEFAULT PASS)"

                    # Momentum check
                    if len(price_history) >= 5:
                        try:
                            momentum_slope = (price_history[-1] - price_history[-5]) / 4
                            momentum_valid = abs(momentum_slope) > 0.5
                            momentum_direction = "UP" if momentum_slope > 0 else "DOWN"
                            momentum_msg = f"Momentum: {momentum_slope:.3f} ({momentum_direction}) ({'PASS' if momentum_valid else 'FAIL'})"
                        except IndexError:
                            momentum_valid = True
                            momentum_msg = "Momentum: Index error (DEFAULT PASS)"
                    else:
                        momentum_valid = True
                        momentum_msg = "Momentum: Insufficient data (DEFAULT PASS)"

                    # Require 2 out of 3 checks to pass
                    step3_checks_passed = sum([volume_valid, acceleration_valid, momentum_valid])
                    step3_valid = step3_checks_passed >= 2
                    
                    # Combined Analysis
                    utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                    time_display = utc_time.strftime("%H:%M:%S")
                    
                    print(f"[{time_display} UTC] COMPLETE ENTRY FLOW ANALYSIS")
                    print("=" * 50)
                    
                    # Get all analysis data
                    if analysis:
                        rsi = analysis.get('rsi', 0)
                        ema9 = analysis.get('ema9', 0)
                        ema21 = analysis.get('ema21', 0)
                        st_dir = analysis.get('supertrend_direction', 0)
                        atr = analysis.get('atr', 0)
                        
                        # Entry conditions
                        buy_rsi = rsi > 45
                        buy_ema = ema9 > ema21  
                        buy_conditions_met = buy_rsi and buy_ema

                        sell_rsi = rsi < 55
                        sell_ema = ema9 < ema21
                        sell_conditions_met = sell_rsi and sell_ema

                        print("STEP 1 - ENTRY CONDITIONS:")
                        print(f"  BUY:  RSI>45={buy_rsi} | EMA9>EMA21={buy_ema} | ST={st_dir} -> {'READY' if buy_conditions_met else 'WAIT'}")
                        print(f"  SELL: RSI<55={sell_rsi} | EMA9<EMA21={sell_ema} | ST={st_dir} -> {'READY' if sell_conditions_met else 'WAIT'}")
                        print(f"  Values: RSI={rsi:.1f} | EMA9={ema9:.2f} | EMA21={ema21:.2f}")

                        if buy_conditions_met:
                            signal = "BUY"
                            entry_conditions_met = True
                        elif sell_conditions_met:
                            signal = "SELL"
                            entry_conditions_met = True
                        else:
                            signal = "NONE"
                            entry_conditions_met = False
                        
                        # Step 2
                        print("\nSTEP 2 - ENTRY LOGIC:")
                        print(f"  Price: {current_price:.2f} | OHLC: {current_candle['open']:.2f}/{current_candle['high']:.2f}/{current_candle['low']:.2f}/{current_candle['close']:.2f}")
                        candle_color = "GREEN" if current_price > current_candle['open'] else "RED" if current_price < current_candle['open'] else "DOJI"
                        print(f"  Candle: {candle_color} {'VALID' if is_valid_candle else 'INVALID'} ({strength_score:.0f}/100) | Breakout: {'VALID' if breakout_valid else 'INVALID'}")
                        print(f"  {breakout_msg}")
                        
                        # Step 3
                        print("\nSTEP 3 - ENTER TRADING:")
                        print(f"  Volume: {'PASS' if volume_valid else 'FAIL'} | Acceleration: {'PASS' if acceleration_valid else 'FAIL'} | Momentum: {'PASS' if momentum_valid else 'FAIL'}")
                        print(f"  {volume_msg}")
                        print(f"  {acceleration_msg}")
                        print(f"  {momentum_msg}")
                        print(f"  Result: {step3_checks_passed}/3 checks passed ({'VALID' if step3_valid else 'INVALID'})")
                        
                        # Step 4
                        print("\nSTEP 4 - ORDER PLACEMENT:")
                        market_data = entry_manager.order_logic.get_market_depth(symbol)
                        if 'error' not in market_data:
                            entry_price, entry_msg = entry_manager.order_logic.calculate_entry_price(symbol, signal)
                            
                            atr_value = analysis.get('atr', 0)
                            if signal == "BUY":
                                stop_loss = current_price - (atr_value * 1.1)
                                take_profit = current_price + (atr_value * 1.1 * 2.0)
                            else:
                                stop_loss = current_price + (atr_value * 1.1)
                                take_profit = current_price - (atr_value * 1.1 * 2.0)
                            
                            volume, volume_msg = entry_manager.order_logic.calculate_position_size(symbol, entry_price, stop_loss)
                            
                            print(f"  Bid: {market_data.get('bid', 0):.5f} | Ask: {market_data.get('ask', 0):.5f} | Spread: {market_data.get('spread', 0):.5f}")
                            print(f"  Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                            print(f"  Volume: {volume} | Risk: $100 | RR: 2:1")
                            
                            order_ready = entry_price > 0 and volume > 0
                            print(f"  Order Ready: {'YES' if order_ready else 'NO'}")
                        else:
                            print(f"  Market data error: {market_data.get('error', 'Unknown')}")
                            order_ready = False
                        
                        # Final decision
                        step1_valid = entry_conditions_met
                        step2_valid = is_valid_candle and breakout_valid
                        step4_valid = order_ready
                        all_systems_go = step1_valid and step2_valid and step3_valid and step4_valid
                        
                        print("\nFINAL DECISION:")
                        if all_systems_go:
                            print(f"  EXECUTE {signal} TRADE NOW - ALL 4 STEPS VALIDATED!")
                        else:
                            print(f"  WAITING: Step1={step1_valid} | Step2={step2_valid} | Step3={step3_valid} | Step4={step4_valid}")
                    
                    else:
                        print("No analysis data available")
            
            else:
                # No new tick - realistic market timing
                # Real market generates 2-3 ticks/sec, so wait ~400ms between checks
                time.sleep(0.4)
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\nAnalysis stopped by user")
        print(f"Runtime: {elapsed:.1f}s | Processed {tick_count} genuine ticks | Rate: {tick_count/elapsed:.1f} ticks/sec")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    market_realistic_trading()