import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def quick_tick_verification():
    """Quick 10-second tick rate verification"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("QUICK TICK VERIFICATION - 10 SECONDS")
    print("=" * 40)
    
    symbol = "XAUUSD"
    last_tick_time = 0
    genuine_ticks = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < 10:  # Run for 10 seconds
            tick = mt5.symbol_info_tick(symbol)
            
            # Only count genuine new ticks
            if tick and tick.time > last_tick_time:
                genuine_ticks += 1
                last_tick_time = tick.time
                elapsed = time.time() - start_time
                rate = genuine_ticks / elapsed if elapsed > 0 else 0
                
                print(f"Tick #{genuine_ticks} | Rate: {rate:.1f}/sec | Price: {tick.bid:.2f}")
            
            time.sleep(0.1)  # Check every 100ms
    
    except KeyboardInterrupt:
        pass
    
    finally:
        elapsed = time.time() - start_time
        rate = genuine_ticks / elapsed if elapsed > 0 else 0
        print(f"\nRESULTS:")
        print(f"Time: {elapsed:.1f}s")
        print(f"Genuine Ticks: {genuine_ticks}")
        print(f"Rate: {rate:.1f} ticks/sec")
        print(f"Expected: 2-3 ticks/sec")
        print(f"Status: {'NORMAL' if 1.5 <= rate <= 4.0 else 'UNUSUAL'}")
        mt5.shutdown()

if __name__ == "__main__":
    quick_tick_verification()