import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def verify_tick_data():
    """Verify if tick data is actually updating or static"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("TICK DATA VERIFICATION")
    print("=" * 50)
    print("Monitoring XAUUSD for 30 seconds...")
    print("Press Ctrl+C to stop early")
    print("=" * 50)
    
    symbol = "XAUUSD"
    tick_count = 0
    unique_ticks = set()
    last_tick_time = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < 30:  # Run for 30 seconds
            tick = mt5.symbol_info_tick(symbol)
            current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
            
            if tick:
                tick_count += 1
                
                # Check if this is a new tick
                is_new_tick = tick.time > last_tick_time
                if is_new_tick:
                    last_tick_time = tick.time
                
                # Track unique price combinations
                price_combo = (tick.bid, tick.ask, tick.time)
                unique_ticks.add(price_combo)
                
                # Show every 10th tick to avoid spam
                if tick_count % 10 == 0:
                    tick_datetime = datetime.fromtimestamp(tick.time)
                    print(f"[{current_time}] Tick #{tick_count:3d} | "
                          f"Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f} | "
                          f"Time: {tick_datetime.strftime('%H:%M:%S')} | "
                          f"{'NEW' if is_new_tick else 'OLD'}")
            
            time.sleep(0.1)  # Check every 100ms
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        mt5.shutdown()
        
        # Analysis
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 50)
        print("TICK ANALYSIS RESULTS:")
        print(f"Duration: {elapsed_time:.1f} seconds")
        print(f"Total Ticks Checked: {tick_count}")
        print(f"Unique Tick Combinations: {len(unique_ticks)}")
        print(f"Ticks per Second: {tick_count/elapsed_time:.1f}")
        
        if len(unique_ticks) == 1:
            print("RESULT: STATIC DATA - All ticks identical (markets likely closed)")
        elif len(unique_ticks) < tick_count * 0.1:
            print("RESULT: LIMITED VARIATION - Very few unique ticks (low activity)")
        else:
            print("RESULT: LIVE DATA - Multiple unique ticks detected")
        
        # Show first and last tick for comparison
        if tick:
            last_tick_datetime = datetime.fromtimestamp(tick.time)
            print(f"Last Tick Timestamp: {last_tick_datetime}")
            print(f"Final Price: Bid={tick.bid:.5f} Ask={tick.ask:.5f}")

if __name__ == "__main__":
    verify_tick_data()