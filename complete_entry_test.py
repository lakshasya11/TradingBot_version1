import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator, MomentumValidator, BreakoutLogic, AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy

def complete_entry_analysis():
    """Combined test: Entry Conditions + Candle Structure Validation"""
    
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
    
    print("🚀 COMPLETE ENTRY ANALYSIS - LIVE TEST")
    print("=" * 70)
    print("Step 1: Entry Conditions | Step 2: Candle Structure Validation")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        while True:
            # Get live market data
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
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
                
                current_price = tick.bid
                
                # Update price history for momentum analysis
                price_history.append(current_price)
                if len(price_history) > 10:  # Keep last 10 prices
                    price_history = price_history[-10:]
                
                # Validate candle structure
                is_valid_candle, candle_msg = validator.validate_strong_green_candle(current_candle, current_price)
                strength_score = validator.get_candle_strength_score(current_candle, current_price)
                breakout_valid, breakout_msg = validator.validate_breakout_structure(current_candle, previous_candle)
                
                # Step 3: Enter Trading validation
                momentum_valid, momentum_msg = momentum_validator.validate_momentum(
                    price_history, 
                    current_price=current_price, 
                    open_price=current_candle['open']
                )
                
                red_candle_valid, red_candle_msg = breakout_logic.check_red_candle_entry(
                    current_candle, previous_candle, current_price
                ) if signal == "SELL" else (True, "Not required for BUY")
                
                # Combined Analysis - Use UTC time
                utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                time_display = utc_time.strftime("%H:%M:%S")
                
                print(f"\n[{time_display} UTC] 🎯 COMPLETE ENTRY FLOW ANALYSIS")
                print("=" * 70)
                
                # Get all analysis data first
                if analysis:
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    atr = analysis.get('atr', 0)
                    
                    # Entry conditions checks
                    rsi_check = rsi > 50 if signal == "BUY" else rsi < 40 if signal == "SELL" else False
                    ema_check = ema9 > ema21 if signal == "BUY" else ema9 < ema21 if signal == "SELL" else False
                    st_check = st_dir == 1 if signal == "BUY" else st_dir == -1 if signal == "SELL" else False
                    
                    entry_conditions_met = rsi_check and ema_check and st_check
                    
                    print("🔍 STEP 1 → ENTRY CONDITIONS:")
                    print(f"  RSI: {rsi:.1f} {'✅' if rsi_check else '❌'} | EMA: {ema9:.2f}/{ema21:.2f} {'✅' if ema_check else '❌'} | ST: {st_dir} {'✅' if st_check else '❌'}")
                    print(f"  └─ Signal: {signal if entry_conditions_met else 'NONE'} {'✅' if entry_conditions_met else '❌'}")
                    
                    # Always show Step 2, Step 3, and Step 4 for complete analysis
                    print("\n🚀 STEP 2 → ENTRY LOGIC:")
                    print(f"  Price: {current_price:.2f} | OHLC: {current_candle['open']:.2f}/{current_candle['high']:.2f}/{current_candle['low']:.2f}/{current_candle['close']:.2f}")
                    print(f"  Candle: {'✅' if is_valid_candle else '❌'} ({strength_score:.0f}/100) | Breakout: {'✅' if breakout_valid else '❌'}")
                    print(f"  └─ {candle_msg[:50]}...")
                    print(f"  └─ {breakout_msg[:50]}...")
                    
                    # Always show Step 3
                    print("\n🎯 STEP 3 → ENTER TRADING:")
                    print(f"  Momentum: {'✅' if momentum_valid else '❌'} | Red Entry: {'✅' if red_candle_valid else '❌'}")
                    print(f"  └─ {momentum_msg[:60]}...")
                    if signal == "SELL":
                        print(f"  └─ {red_candle_msg[:60]}...")
                    
                    # Step 4: Order Placement Analysis
                    print("\n💰 STEP 4 → ORDER PLACEMENT:")
                    
                    # Get market data for Step 4
                    market_data = entry_manager.order_logic.get_market_depth(symbol)
                    if 'error' not in market_data:
                        entry_price, entry_msg = entry_manager.order_logic.calculate_entry_price(symbol, signal)
                        
                        # Calculate stop loss using ATR
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
                        print(f"  Order Ready: {'✅' if order_ready else '❌'}")
                    else:
                        print(f"  ❌ Market data error: {market_data.get('error', 'Unknown')}")
                        order_ready = False
                    
                    # Final decision based on all 4 steps
                    step1_valid = entry_conditions_met
                    step2_valid = is_valid_candle and breakout_valid
                    step3_valid = momentum_valid and red_candle_valid
                    step4_valid = order_ready
                    all_systems_go = step1_valid and step2_valid and step3_valid and step4_valid
                    
                    print("\n🚀 FINAL DECISION:")
                    if all_systems_go:
                        print(f"  🎆 EXECUTE {signal} TRADE NOW - ALL 4 STEPS VALIDATED!")
                        print(f"  ✅ Ready for live order execution")
                        
                        # Uncomment below to actually place orders (DEMO ONLY)
                        # result = entry_manager.execute_advanced_entry(
                        #     symbol, signal, current_candle, previous_candle, 
                        #     current_price, price_history, analysis.get('atr', 0)
                        # )
                        # print(f"  Order Result: {result.get('message', 'Unknown')}")
                        
                    else:
                        failed_steps = []
                        if not step1_valid: failed_steps.append("Step 1 (Entry Conditions)")
                        if not step2_valid: failed_steps.append("Step 2 (Entry Logic)")
                        if not step3_valid: failed_steps.append("Step 3 (Enter Trading)")
                        if not step4_valid: failed_steps.append("Step 4 (Order Placement)")
                        print(f"  ⏳ WAIT - Failed: {', '.join(failed_steps)}")
                else:
                    print("❌ No market data available")
                    print("\n🔒 STEP 2 → SKIPPED (No data)")
                    print("🔒 STEP 3 → SKIPPED (No data)")
                    print("🔒 STEP 4 → SKIPPED (No data)")
                    print("\n🚀 FINAL DECISION:")
                    print("  ⏳ WAIT - No market data available")
                
                print("=" * 70)
                
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n\n✅ Complete entry analysis stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    complete_entry_analysis()