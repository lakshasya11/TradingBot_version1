import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator

def live_candle_validation():
    """Test candle validation with live MT5 data"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    validator = CandleStructureValidator()
    
    print("🔴 LIVE CANDLE STRUCTURE VALIDATION")
    print("=" * 60)
    print("Testing with real XAUUSD data - Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        while True:
            # Get live data
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) >= 2 and tick:
                df = pd.DataFrame(rates)
                
                # Current and previous candles
                current_candle = {
                    'open': df.iloc[-1]['open'],
                    'close': df.iloc[-1]['close'],
                    'high': df.iloc[-1]['high'],
                    'low': df.iloc[-1]['low'],
                    'time': pd.to_datetime(df.iloc[-1]['time'], unit='s')
                }
                
                previous_candle = {
                    'open': df.iloc[-2]['open'],
                    'close': df.iloc[-2]['close'],
                    'high': df.iloc[-2]['high'],
                    'low': df.iloc[-2]['low']
                }
                
                # Use current bid price as live price
                current_price = tick.bid
                
                # Test candle structure
                is_valid, message = validator.validate_strong_green_candle(current_candle, current_price)
                strength_score = validator.get_candle_strength_score(current_candle, current_price)
                
                # Test breakout structure
                breakout_valid, breakout_msg = validator.validate_breakout_structure(current_candle, previous_candle)
                
                # Display results
                now = datetime.now().strftime("%H:%M:%S")
                
                print(f"\r[{now}] XAUUSD Live Analysis:", end="")
                print(f"\n  💰 Price: {current_price:.2f} | Open: {current_candle['open']:.2f} | High: {current_candle['high']:.2f} | Low: {current_candle['low']:.2f}")
                print(f"  🟢 Candle: {'✅ VALID' if is_valid else '❌ INVALID'} | Score: {strength_score:.1f}/100")
                print(f"  📊 {message}")
                print(f"  🎯 Breakout: {'✅ VALID' if breakout_valid else '❌ INVALID'}")
                print(f"  📈 {breakout_msg}")
                print("-" * 60)
                
            time.sleep(1)  # Update every 1 second
            
    except KeyboardInterrupt:
        print("\n\n✅ Live testing stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    live_candle_validation()