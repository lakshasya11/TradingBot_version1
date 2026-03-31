import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def live_tick_monitor():
    """Direct live tick monitoring for XAUUSD"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("LIVE TICK MONITOR - XAUUSD")
    print("=" * 40)
    print("Monitoring every tick change...")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    
    symbol = "XAUUSD"
    last_tick_time = 0
    last_price = 0
    tick_count = 0
    start_time = time.time()
    
    try:
        while True:
            tick = mt5.symbol_info_tick(symbol)
            current_time = time.time()
            
            if tick:
                # Check for ANY change (time OR price)
                price_changed = abs(tick.bid - last_price) > 0.001 if last_price > 0 else True
                time_changed = tick.time > last_tick_time
                
                if time_changed or price_changed:
                    tick_count += 1
                    elapsed = current_time - start_time
                    rate = tick_count / elapsed if elapsed > 0 else 0
                    
                    # Show current time vs tick time
                    current_dt = datetime.now()
                    tick_dt = datetime.fromtimestamp(tick.time)
                    time_diff = (current_dt - tick_dt).total_seconds()
                    
                    price_diff = tick.bid - last_price if last_price > 0 else 0
                    
                    print(f"Tick #{tick_count:3d} | "
                          f"Price: {tick.bid:.2f} ({price_diff:+.3f}) | "
                          f"Time: {tick_dt.strftime('%H:%M:%S')} | "
                          f"Delay: {time_diff:.1f}s | "
                          f"Rate: {rate:.1f}/sec")
                    
                    last_tick_time = tick.time
                    last_price = tick.bid
            
            time.sleep(0.05)  # Check every 50ms for maximum responsiveness
    
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        final_rate = tick_count / elapsed if elapsed > 0 else 0
        print(f"\nSUMMARY:")
        print(f"Duration: {elapsed:.1f}s")
        print(f"Total Ticks: {tick_count}")
        print(f"Final Rate: {final_rate:.1f} ticks/sec")
        print(f"Status: {'LIVE' if final_rate > 1.0 else 'SLOW/INACTIVE'}")
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    live_tick_monitor()