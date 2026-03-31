import MetaTrader5 as mt5
import os
import subprocess
import time

def check_mt5_setup():
    print("🔍 CHECKING MT5 SETUP...")
    
    # Check if MT5 executable exists
    mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    
    if os.path.exists(mt5_path):
        print(f"✅ MT5 found at: {mt5_path}")
    else:
        print(f"❌ MT5 not found at: {mt5_path}")
        # Try alternative paths
        alt_paths = [
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            r"C:\Users\{}\AppData\Roaming\MetaQuotes\Terminal\*.exe".format(os.getenv('USERNAME'))
        ]
        for path in alt_paths:
            if os.path.exists(path):
                print(f"✅ Found MT5 at: {path}")
                mt5_path = path
                break
    
    # Try to start MT5 if not running
    print("\n🚀 STARTING MT5...")
    try:
        subprocess.Popen([mt5_path])
        print("✅ MT5 started successfully")
        time.sleep(5)  # Wait for MT5 to load
    except Exception as e:
        print(f"❌ Failed to start MT5: {e}")
    
    # Try to initialize
    print("\n🔌 TESTING CONNECTION...")
    
    # Try with path specification
    if not mt5.initialize(path=mt5_path):
        print("❌ MT5 initialization with path failed")
        # Try without path
        if not mt5.initialize():
            print("❌ MT5 initialization failed completely")
            print("💡 SOLUTIONS:")
            print("   1. Make sure MT5 is running")
            print("   2. Run this script as Administrator")
            print("   3. Check if MT5 path is correct")
            return False
        else:
            print("✅ MT5 initialized without path")
    else:
        print("✅ MT5 initialized with path")
    
    # Test login
    print("\n🔑 TESTING LOGIN...")
    login = 30171661
    password = "Kank$544"
    server = "Winprofx-Live"
    
    if mt5.login(login, password, server):
        print("✅ Login successful!")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"📊 Account: {account_info.name}")
            print(f"💰 Balance: ${account_info.balance:.2f}")
            print(f"💎 Equity: ${account_info.equity:.2f}")
        
        # Test symbol data
        symbol = "EURUSD"
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"📈 {symbol} - Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
        
        mt5.shutdown()
        print("\n🎉 ALL TESTS PASSED - READY FOR TRADING!")
        return True
    else:
        print(f"❌ Login failed: {mt5.last_error()}")
        print("💡 Check your credentials in .env file")
        mt5.shutdown()
        return False

if __name__ == "__main__":
    check_mt5_setup()