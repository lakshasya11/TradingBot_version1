import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone, timedelta
import time
import os
from dotenv import load_dotenv

def relaxed_trading_test():
    """Relaxed conditions for testing - will generate more trades"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("🚀 RELAXED TRADING TEST - MORE TRADES WILL EXECUTE")
    print("=" * 60)
    print("⚠️  This is for TESTING only - uses relaxed conditions")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    symbol = "XAUUSD"
    previous_price = None
    tick_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Get live market data
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                current_price = (tick.bid + tick.ask) / 2
                price_changed = (previous_price is None or 
                               abs(current_price - previous_price) > 0.0001)
                
                if price_changed:
                    tick_count += 1
                    previous_price = current_price
                    
                    # Show every 10th tick for faster feedback
                    if tick_count % 10 == 0:
                        print(f"\n[TICK #{tick_count}] Price: {current_price:.2f}")
                        
                        # RELAXED CONDITIONS - Much easier to trigger
                        
                        # Step 1: Simple price direction (relaxed)
                        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 2)
                        if rates is not None and len(rates) >= 2:
                            current_candle = rates[-1]
                            prev_candle = rates[-2]
                            
                            # Simple trend detection
                            price_rising = current_price > prev_candle['close']
                            signal = "BUY" if price_rising else "SELL"
                            step1_valid = True  # Always pass for testing
                            
                            # Step 2: Simple candle check (relaxed)
                            candle_size = abs(current_candle['high'] - current_candle['low'])
                            step2_valid = candle_size > 0.5  # Any candle with 50 cent range
                            
                            # Step 3: Simple momentum (relaxed)
                            step3_valid = True  # Always pass for testing
                            
                            # Step 4: Order setup
                            entry_price = tick.ask if signal == "BUY" else tick.bid
                            atr_value = 2.0  # Fixed ATR for testing
                            
                            if signal == "BUY":
                                stop_loss = entry_price - atr_value
                                take_profit = entry_price + (atr_value * 2)
                            else:
                                stop_loss = entry_price + atr_value
                                take_profit = entry_price - (atr_value * 2)
                            
                            volume = 0.01
                            step4_valid = entry_price > 0
                            
                            # Final decision
                            all_systems_go = step1_valid and step2_valid and step3_valid and step4_valid
                            
                            print(f"RELAXED TEST: {signal} Signal")
                            print(f"  Step1: {step1_valid} | Step2: {step2_valid} | Step3: {step3_valid} | Step4: {step4_valid}")
                            print(f"  Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                            print(f"  Execute: {'YES' if all_systems_go else 'NO'}")
                            
                            if all_systems_go:
                                # Check existing positions
                                existing_positions = mt5.positions_get(symbol=symbol)
                                if existing_positions:
                                    print(f"  [BLOCKED] Already in position")
                                else:
                                    # Execute trade
                                    result = mt5.order_send({
                                        'action': mt5.TRADE_ACTION_DEAL,
                                        'symbol': symbol,
                                        'volume': volume,
                                        'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                                        'price': entry_price,
                                        'sl': stop_loss,
                                        'tp': take_profit,
                                        'comment': 'Relaxed Test Trade',
                                        'type_filling': mt5.ORDER_FILLING_IOC,
                                        'magic': 777777,
                                        'deviation': 0
                                    })
                                    
                                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                        print(f"  ✅ TRADE EXECUTED: Ticket #{result.order}")
                                        print(f"  📊 Check MT5 Trade tab now!")
                                    else:
                                        error_msg = result.comment if result else "Unknown error"
                                        print(f"  ❌ Trade failed: {error_msg}")
                    
                    time.sleep(0.5)  # Half second pause for testing
            else:
                time.sleep(0.01)
                
    except KeyboardInterrupt:
        print(f"\n\nRelaxed test stopped")
        
        # Show current positions
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            print(f"\nCURRENT POSITIONS:")
            for pos in positions:
                pos_type = "BUY" if pos.type == 0 else "SELL"
                print(f"  Ticket #{pos.ticket}: {pos_type} {pos.volume} lots | P&L: ${pos.profit:.2f}")
        else:
            print("\nNo open positions")
            
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    relaxed_trading_test()