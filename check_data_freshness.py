import MetaTrader5 as mt5
from datetime import datetime

def check_data_freshness():
    """Check if MT5 is getting current data"""
    
    if not mt5.initialize():
        print(f"❌ MT5 connection failed: {mt5.last_error()}")
        return
    
    print("🔍 Checking MT5 data freshness...")
    print("=" * 50)
    
    # Get current system time
    now = datetime.now()
    print(f"Current system time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test multiple symbols
    symbols = ["XAUUSD", "EURUSD", "GBPUSD"]
    
    for symbol in symbols:
        print(f"\n📊 Testing {symbol}:")
        
        # Get latest tick
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            tick_time = datetime.fromtimestamp(tick.time)
            time_diff = (now - tick_time).total_seconds()
            
            print(f"  Latest tick time: {tick_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}")
            print(f"  Age: {time_diff:.0f} seconds")
            
            if time_diff < 300:  # Less than 5 minutes old
                print(f"  Status: ✅ FRESH DATA")
            elif time_diff < 3600:  # Less than 1 hour old
                print(f"  Status: ⚠️ SLIGHTLY OLD")
            else:
                print(f"  Status: ❌ VERY OLD DATA")
        else:
            print(f"  Status: ❌ NO TICK DATA")
        
        # Get latest bar
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
        if rates:
            bar_time = datetime.fromtimestamp(rates[0]['time'])
            bar_age = (now - bar_time).total_seconds()
            
            print(f"  Latest bar time: {bar_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Bar age: {bar_age:.0f} seconds")
            
            if bar_age < 120:  # Less than 2 minutes
                print(f"  Bar status: ✅ CURRENT")
            else:
                print(f"  Bar status: ❌ OLD (stuck at {bar_time.strftime('%Y-%m-%d')})")
        else:
            print(f"  Bar status: ❌ NO BAR DATA")
    
    # Check account info
    account = mt5.account_info()
    if account:
        print(f"\n👤 Account: {account.login} | Server: {account.server}")
        print(f"Balance: ${account.balance:.2f} | Equity: ${account.equity:.2f}")
    
    mt5.shutdown()

if __name__ == "__main__":
    check_data_freshness()