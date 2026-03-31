import MetaTrader5 as mt5
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

def check_market_status():
    """Check if markets are currently active"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("MARKET STATUS CHECKER")
    print("=" * 30)
    
    symbols = ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"]
    
    for symbol in symbols:
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if symbol_info and tick:
            # Check if market is open
            current_time = datetime.now()
            tick_time = datetime.fromtimestamp(tick.time)
            time_diff = (current_time - tick_time).total_seconds()
            
            is_active = time_diff < 60  # Active if tick is within 1 minute
            
            print(f"{symbol}:")
            print(f"  Price: {tick.bid:.5f}")
            print(f"  Last Tick: {tick_time.strftime('%H:%M:%S')}")
            print(f"  Status: {'ACTIVE' if is_active else 'INACTIVE'}")
            print(f"  Spread: {tick.ask - tick.bid:.5f}")
            print()
        else:
            print(f"{symbol}: NOT AVAILABLE")
    
    mt5.shutdown()

if __name__ == "__main__":
    check_market_status()