import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator, MomentumValidator, BreakoutLogic, AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy

def diagnose_trade_conditions():
    """Diagnostic tool to identify why trades aren't executing"""
    
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
    
    price_history = []
    step_failures = {"step1": 0, "step2": 0, "step3": 0, "step4": 0}
    total_checks = 0
    
    print("🔍 TRADE EXECUTION DIAGNOSTIC")
    print("=" * 60)
    print("Analyzing why trades aren't executing...")
    print("Press Ctrl+C to stop and see summary")
    print("=" * 60)
    
    try:
        while True:
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) >= 2 and tick:
                total_checks += 1
                df = pd.DataFrame(rates)
                
                # Get analysis data
                analysis = strategy.analyze_timeframe("M1")
                signal = strategy.check_entry_conditions(analysis)
                
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
                price_history.append(current_price)
                if len(price_history) > 10:
                    price_history = price_history[-10:]
                
                # UTC time
                utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                time_display = utc_time.strftime("%H:%M:%S")
                
                # STEP 1 ANALYSIS
                if analysis:
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    
                    # Check individual conditions
                    rsi_buy = rsi > 50
                    rsi_sell = rsi < 40
                    ema_buy = ema9 > ema21
                    ema_sell = ema9 < ema21
                    st_buy = st_dir == 1
                    st_sell = st_dir == -1
                    
                    buy_conditions = rsi_buy and ema_buy and st_buy
                    sell_conditions = rsi_sell and ema_sell and st_sell
                    step1_valid = buy_conditions or sell_conditions
                    
                    if buy_conditions:
                        signal = "BUY"
                    elif sell_conditions:
                        signal = "SELL"
                    else:
                        signal = "NONE"
                        step_failures["step1"] += 1
                    
                    # STEP 2 ANALYSIS
                    is_valid_candle, candle_msg = validator.validate_strong_green_candle(current_candle, current_price)
                    breakout_valid, breakout_msg = validator.validate_breakout_structure(current_candle, previous_candle)
                    step2_valid = is_valid_candle and breakout_valid
                    if not step2_valid:
                        step_failures["step2"] += 1
                    
                    # STEP 3 ANALYSIS
                    momentum_valid, momentum_msg = momentum_validator.validate_momentum(
                        price_history, current_price=current_price, open_price=current_candle['open']
                    )
                    red_candle_valid, red_candle_msg = breakout_logic.check_red_candle_entry(
                        current_candle, previous_candle, current_price
                    ) if signal == "SELL" else (True, "Not required for BUY")
                    
                    step3_valid = momentum_valid and red_candle_valid
                    if not step3_valid:
                        step_failures["step3"] += 1
                    
                    # STEP 4 ANALYSIS
                    market_data = entry_manager.order_logic.get_market_depth(symbol)
                    step4_valid = 'error' not in market_data
                    if not step4_valid:
                        step_failures["step4"] += 1
                    
                    # Show detailed failure reasons every 10 seconds
                    if total_checks % 10 == 0:
                        print(f"\n[{time_display} UTC] 📊 DIAGNOSTIC SUMMARY (Last 10 checks)")
                        print(f"Signal: {signal} | Price: {current_price:.2f}")
                        
                        # Step 1 details
                        print(f"STEP 1: RSI={rsi:.1f} ({'✅' if rsi_buy else '❌' if signal=='BUY' else '⚪'}/{'✅' if rsi_sell else '❌' if signal=='SELL' else '⚪'}) | EMA={ema9:.2f}/{ema21:.2f} ({'✅' if ema_buy else '❌' if signal=='BUY' else '⚪'}/{'✅' if ema_sell else '❌' if signal=='SELL' else '⚪'}) | ST={st_dir} ({'✅' if st_buy else '❌' if signal=='BUY' else '⚪'}/{'✅' if st_sell else '❌' if signal=='SELL' else '⚪'})")
                        
                        # Step 2 details
                        strength_score = validator.get_candle_strength_score(current_candle, current_price)
                        print(f"STEP 2: Candle={'✅' if is_valid_candle else '❌'} (Score: {strength_score:.0f}/100) | Breakout={'✅' if breakout_valid else '❌'}")
                        
                        # Step 3 details
                        print(f"STEP 3: Momentum={'✅' if momentum_valid else '❌'} | Red Entry={'✅' if red_candle_valid else '❌'}")
                        
                        # Step 4 details
                        print(f"STEP 4: Market Data={'✅' if step4_valid else '❌'}")
                        
                        # Overall status
                        all_valid = step1_valid and step2_valid and step3_valid and step4_valid
                        print(f"RESULT: {'🎆 TRADE READY' if all_valid else '⏳ WAITING'}")
                        
                        if not all_valid:
                            failed = []
                            if not step1_valid: failed.append("Entry Conditions")
                            if not step2_valid: failed.append("Candle Structure")
                            if not step3_valid: failed.append("Momentum")
                            if not step4_valid: failed.append("Market Data")
                            print(f"Failed: {', '.join(failed)}")
                        
                        print("-" * 60)
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n\n📈 DIAGNOSTIC RESULTS ({total_checks} total checks)")
        print("=" * 50)
        print(f"Step 1 Failures: {step_failures['step1']} ({step_failures['step1']/total_checks*100:.1f}%)")
        print(f"Step 2 Failures: {step_failures['step2']} ({step_failures['step2']/total_checks*100:.1f}%)")
        print(f"Step 3 Failures: {step_failures['step3']} ({step_failures['step3']/total_checks*100:.1f}%)")
        print(f"Step 4 Failures: {step_failures['step4']} ({step_failures['step4']/total_checks*100:.1f}%)")
        
        # Identify main bottleneck
        max_failures = max(step_failures.values())
        bottleneck = [k for k, v in step_failures.items() if v == max_failures][0]
        print(f"\n🎯 MAIN BOTTLENECK: {bottleneck.upper()} ({max_failures} failures)")
        
        if bottleneck == "step1":
            print("💡 SOLUTION: Relax RSI thresholds (RSI>45 for BUY, RSI<55 for SELL)")
        elif bottleneck == "step2":
            print("💡 SOLUTION: Lower candle strength requirements")
        elif bottleneck == "step3":
            print("💡 SOLUTION: Reduce momentum validation strictness")
        else:
            print("💡 SOLUTION: Check MT5 connection and market data")
            
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    diagnose_trade_conditions()