import MetaTrader5 as mt5
from datetime import datetime
import os
from dotenv import load_dotenv

def verify_mt5_time():
    """Verify current MT5 time"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("MT5 TIME VERIFICATION")
    print("=" * 25)
    
    # Get current tick for XAUUSD
    tick = mt5.symbol_info_tick("XAUUSD")
    
    if tick:
        # MT5 server time
        mt5_time = datetime.fromtimestamp(tick.time)
        
        # Local system time
        local_time = datetime.now()
        
        print(f"MT5 Server Time: {mt5_time.strftime('%H:%M:%S')}")
        print(f"Local Time:      {local_time.strftime('%H:%M:%S')}")
        print(f"XAUUSD Price:    {tick.bid:.2f}")
        print(f"Last Update:     {mt5_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check if time matches what user sees
        mt5_hour_min = mt5_time.strftime('%H:%M')
        print(f"\nMT5 Time (H:M):  {mt5_hour_min}")
        print(f"User Reports:    8:17")
        print(f"Match:           {'YES' if mt5_hour_min.startswith('8:17') or mt5_hour_min == '08:17' else 'NO'}")
        
    else:
        print("No tick data available for XAUUSD")
    
    mt5.shutdown()

if __name__ == "__main__":
    verify_mt5_time()