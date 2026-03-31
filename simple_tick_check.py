import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def simple_tick_verification():
    """Simple tick verification - shows only tick values and rates"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("TICK VERIFICATION - XAUUSD")
    print("=" * 30)
    print("Press Ctrl+C to stop")
    print("=" * 30)
    
    symbol = "XAUUSD"
    last_tick_time = 0
    tick_count = 0
    start_time = time.time()
    
    try:
        while True:
            tick = mt5.symbol_info_tick(symbol)
            current_time = time.time()
            
            # Only process genuine new ticks
            if tick and tick.time > last_tick_time:
                tick_count += 1
                elapsed = current_time - start_time
                rate = tick_count / elapsed if elapsed > 0 else 0
                last_tick_time = tick.time
                
                # Show tick info
                tick_time = datetime.fromtimestamp(tick.time).strftime("%H:%M:%S")
                print(f"Tick #{tick_count:3d} | {tick_time} | Bid: {tick.bid:.2f} | Ask: {tick.ask:.2f} | Rate: {rate:.1f}/sec")
            
            time.sleep(0.1)  # Check every 100ms
    
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        final_rate = tick_count / elapsed if elapsed > 0 else 0
        print(f"\nSUMMARY:")
        print(f"Time: {elapsed:.1f}s")
        print(f"Ticks: {tick_count}")
        print(f"Rate: {final_rate:.1f} ticks/sec")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    simple_tick_verification()