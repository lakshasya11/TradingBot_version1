import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator, MomentumValidator, BreakoutLogic, AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy
from trade_logger import TradeLogger

def complete_entry_analysis():
    """Live Trading System - Fixed Version"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    # Account safety check
    account_info = mt5.account_info()
    if account_info and account_info.trade_mode != 0:  # Live account
        print("LIVE ACCOUNT DETECTED!")
        confirm = input("Type 'LIVE' to confirm: ")
        if confirm != 'LIVE':
            print("Trading cancelled")
            return

    # Initialize components
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    validator = CandleStructureValidator()
    momentum_validator = MomentumValidator()
    breakout_logic = BreakoutLogic()
    entry_manager = AdvancedEntryManager()
    logger = TradeLogger()
    
    # Price history for momentum analysis
    price_history = []
    
    print("LIVE TRADING SYSTEM ACTIVE")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Track genuine price changes only
    previous_price = None
    tick_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Get live market data
            symbol = "XAUUSD"
            tick = mt5.symbol_info_tick(symbol)
            
            # Calculate current price and check for genuine change
            if tick:
                current_price = (tick.bid + tick.ask) / 2
                price_changed = (previous_price is None or 
                               abs(current_price - previous_price) > 0.0001)
                
            # ONLY process genuine PRICE CHANGES
            if tick and price_changed:
                tick_count += 1
                previous_price = current_price
                current_time = time.time()
                tick_rate = tick_count / (current_time - start_time) if current_time > start_time else 0
                
                # Show tick info
                server_time = datetime.fromtimestamp(tick.time)
                local_time = server_time - timedelta(hours=5, minutes=30)
                price_diff = abs(current_price - previous_price) if previous_price else 0
                print(f"\n[TICK #{tick_count}] MT5: {local_time.strftime('%H:%M:%S')} | Price: {current_price:.5f} | D{price_diff:.4f} | Rate: {tick_rate:.1f}/sec")
                
                # Show market status every 5th tick
                if tick_count % 5 == 0:
                    print(f"MARKET: Bid={tick.bid:.5f} | Ask={tick.ask:.5f} | Spread={(tick.ask-tick.bid):.5f}")
                
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            
            if rates is not None and len(rates) >= 2 and tick:
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
                
                # Update price history
                price_history.append(current_price)
                if len(price_history) > 10:
                    price_history = price_history[-10:]
                
                # Validate candle structure
                is_valid_candle, candle_msg = validator.validate_strong_green_candle(current_candle, current_price)
                strength_score = validator.get_candle_strength_score(current_candle, current_price)
                
                # Breakout logic
                prev_close = previous_candle['close']
                breakout_valid = current_price > prev_close if signal == "BUY" else current_price < prev_close
                breakout_msg = f"Price {current_price:.2f} vs prev close {prev_close:.2f}"
                
                # Step 3: Volume, Acceleration, Momentum validation
                extended_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 10)
                extended_df = pd.DataFrame(extended_rates) if extended_rates is not None else df

                # Volume check
                current_volume = df.iloc[-1]['tick_volume']
                avg_volume = extended_df['tick_volume'].tail(5).mean()
                volume_valid = current_volume > (avg_volume * 1.2)
                volume_msg = f"Volume: {current_volume} vs Avg: {avg_volume:.0f} ({'OK' if volume_valid else 'FAIL'})"

                # Acceleration check
                if len(price_history) >= 7:
                    try:
                        recent_changes = [price_history[i] - price_history[i-1] for i in range(-3, 0)]
                        earlier_changes = [price_history[i] - price_history[i-1] for i in range(-6, -3)]
                        recent_avg = sum(abs(x) for x in recent_changes) / len(recent_changes)
                        earlier_avg = sum(abs(x) for x in earlier_changes) / len(earlier_changes)
                        acceleration_valid = recent_avg > (earlier_avg * 1.1)
                        acceleration_msg = f"Acceleration: Recent={recent_avg:.3f} vs Earlier={earlier_avg:.3f} ({'OK' if acceleration_valid else 'FAIL'})"
                    except:
                        acceleration_valid = True
                        acceleration_msg = "Acceleration: Default pass"
                else:
                    acceleration_valid = True
                    acceleration_msg = "Acceleration: Insufficient data (OK)"

                # Momentum check
                if len(price_history) >= 5:
                    try:
                        momentum_slope = (price_history[-1] - price_history[-5]) / 4
                        momentum_valid = abs(momentum_slope) > 0.5
                        momentum_direction = "UP" if momentum_slope > 0 else "DOWN"
                        momentum_msg = f"Momentum: {momentum_slope:.3f} ({momentum_direction}) ({'OK' if momentum_valid else 'FAIL'})"
                    except:
                        momentum_valid = True
                        momentum_msg = "Momentum: Default pass"
                else:
                    momentum_valid = True
                    momentum_msg = "Momentum: Insufficient data (OK)"

                # Require 2 out of 3 checks to pass
                step3_checks_passed = sum([volume_valid, acceleration_valid, momentum_valid])
                step3_valid = step3_checks_passed >= 2
                
                # Convert time
                mt5_server_time = datetime.fromtimestamp(rates[-1]['time'])
                local_mt5_time = mt5_server_time - timedelta(hours=5, minutes=30)
                time_display = local_mt5_time.strftime("%H:%M:%S")
                
                print(f"\n[{time_display} MT5] COMPLETE ENTRY FLOW ANALYSIS")
                print("=" * 50)
                
                # Get analysis data
                if analysis:
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    atr = analysis.get('atr', 0)
                    
                    # Trading conditions
                    buy_rsi = rsi > 45
                    buy_ema = ema9 > ema21  
                    buy_conditions_met = buy_rsi and buy_ema

                    sell_rsi = rsi < 55
                    sell_ema = ema9 < ema21
                    sell_conditions_met = sell_rsi and sell_ema

                    print("STEP 1 -> ENTRY CONDITIONS:")
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
                    
                    print("\nSTEP 2 -> ENTRY LOGIC:")
                    print(f"  Price: {current_price:.2f} | OHLC: {current_candle['open']:.2f}/{current_candle['high']:.2f}/{current_candle['low']:.2f}/{current_candle['close']:.2f}")
                    
                    candle_color = "GREEN" if current_price > current_candle['open'] else "RED" if current_price < current_candle['open'] else "DOJI"
                    
                    print(f"  Candle: {candle_color} {'VALID' if is_valid_candle else 'INVALID'} ({strength_score:.0f}/100) | Breakout: {'VALID' if breakout_valid else 'INVALID'}")
                    print(f"  -> {candle_msg[:50]}...")
                    print(f"  -> {breakout_msg[:50]}...")
                    
                    print("\nSTEP 3 -> ENTER TRADING:")
                    print(f"  Volume: {'PASS' if volume_valid else 'FAIL'} | Acceleration: {'PASS' if acceleration_valid else 'FAIL'} | Momentum: {'PASS' if momentum_valid else 'FAIL'}")
                    print(f"  -> {volume_msg}")
                    print(f"  -> {acceleration_msg}")
                    print(f"  -> {momentum_msg}")
                    print(f"  -> Result: {step3_checks_passed}/3 checks passed ({'VALID' if step3_valid else 'INVALID'})")
                    
                    # Step 4: Order Placement
                    print("\nSTEP 4 -> ORDER PLACEMENT:")
                    
                    market_data = entry_manager.order_logic.get_market_depth(symbol)
                    if 'error' not in market_data:
                        # Calculate tick-based entry price
                        tick_info = mt5.symbol_info_tick(symbol)
                        symbol_info = mt5.symbol_info(symbol)
                        if tick_info and symbol_info:
                            tick_size = symbol_info.trade_tick_size
                            if signal == "BUY":
                                entry_price = tick_info.ask + tick_size
                            elif signal == "SELL":
                                entry_price = tick_info.bid - tick_size
                            else:
                                entry_price = 0
                        else:
                            entry_price = 0
                        
                        # Calculate stop loss using ATR
                        atr_value = analysis.get('atr', 0)
                        if signal == "BUY":
                            stop_loss = current_price - (atr_value * 1.1)
                            take_profit = current_price + (atr_value * 1.1 * 2.0)
                        else:
                            stop_loss = current_price + (atr_value * 1.1)
                            take_profit = current_price - (atr_value * 1.1 * 2.0)
                        
                        raw_volume, volume_msg_calc = entry_manager.order_logic.calculate_position_size(symbol, entry_price, stop_loss)
                        
                        # Validate volume
                        if symbol_info:
                            min_vol = symbol_info.volume_min
                            volume_step = symbol_info.volume_step
                            volume = max(min_vol, round(raw_volume / volume_step) * volume_step)
                        else:
                            volume = 0.01
                        
                        print(f"  Bid: {market_data.get('bid', 0):.5f} | Ask: {market_data.get('ask', 0):.5f} | Spread: {market_data.get('spread', 0):.5f}")
                        print(f"  Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                        print(f"  Volume: {volume} | Risk: $100 | RR: 2:1")
                        
                        order_ready = entry_price > 0 and volume > 0
                        print(f"  Order Ready: {'YES' if order_ready else 'NO'}")
                    else:
                        print(f"  Market data error: {market_data.get('error', 'Unknown')}")
                        order_ready = False
                    
                    # FINAL DECISION
                    step1_valid = entry_conditions_met
                    step2_valid = is_valid_candle and breakout_valid
                    step4_valid = order_ready
                    all_systems_go = step1_valid and step2_valid and step3_valid and step4_valid
                    
                    print("\nFINAL DECISION:")
                    if all_systems_go:
                        print(f"  [OK] EXECUTE {signal} TRADE NOW - ALL 4 STEPS VALIDATED!")
                        final_decision = "EXECUTE"
                        
                        # LIVE TRADING ENABLED
                        result = mt5.order_send({
                            'action': mt5.TRADE_ACTION_DEAL,
                            'symbol': symbol,
                            'volume': volume,
                            'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                            'price': entry_price,
                            'sl': stop_loss,
                            'tp': take_profit,
                            'comment': '4-Step Validated Trade',
                            'type_filling': mt5.ORDER_FILLING_IOC,
                            'magic': 123456
                        })
                        
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            print(f"  [OK] LIVE TRADE EXECUTED: Ticket #{result.order} at {result.price:.5f}")
                        else:
                            error_msg = result.comment if result else "Unknown error"
                            print(f"  [X] TRADE FAILED: {error_msg}")
                        
                    else:
                        print(f"  WAITING: Step1={step1_valid} | Step2={step2_valid} | Step3={step3_valid} | Step4={step4_valid}")
                        final_decision = "WAIT"
                    
                    # LOG TRADE DECISION
                    log_data = {
                        'signal': signal,
                        'price': current_price,
                        'rsi': rsi,
                        'ema9': ema9,
                        'ema21': ema21,
                        'step1': step1_valid,
                        'step2': step2_valid,
                        'step3': step3_valid,
                        'step4': step4_valid,
                        'final_decision': final_decision,
                        'entry_price': entry_price if 'entry_price' in locals() else 0,
                        'stop_loss': stop_loss if 'stop_loss' in locals() else 0,
                        'take_profit': take_profit if 'take_profit' in locals() else 0,
                        'volume': volume if 'volume' in locals() else 0,
                        'candle_color': candle_color,
                        'breakout_valid': breakout_valid,
                        'volume_check': volume_valid,
                        'acceleration_check': acceleration_valid,
                        'momentum_check': momentum_valid
                    }
                    logger.log_trade_decision(log_data)
                
                else:
                    print("No analysis data available")
            else:
                time.sleep(0.05)
            
    except KeyboardInterrupt:
        elapsed_time = time.time() - start_time
        actual_tick_rate = tick_count / elapsed_time if elapsed_time > 0 else 0
        print(f"\n\nAnalysis stopped by user")
        print(f"PERFORMANCE SUMMARY:")
        print(f"   Runtime: {elapsed_time:.1f} seconds")
        print(f"   Genuine Ticks Processed: {tick_count}")
        print(f"   Actual Tick Rate: {actual_tick_rate:.1f} ticks/sec")
        
        print(logger.get_stats())
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    complete_entry_analysis()