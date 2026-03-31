import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from datetime import datetime

def verify_account_expiration():
    """
    Comprehensive test to verify if MT5 account is expired
    """
    load_dotenv()
    
    # Get credentials
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    mt5_path = os.getenv("MT5_PATH")
    
    print("=" * 60)
    print("🔍 MT5 ACCOUNT EXPIRATION VERIFICATION")
    print("=" * 60)
    print(f"Testing Account: {mt5_login}")
    print(f"Server: {mt5_server}")
    print(f"Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Test 1: Try to initialize with credentials
    print("TEST 1: Direct Login Attempt")
    print("-" * 30)
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        error_code, error_msg = mt5.last_error()
        print(f"❌ LOGIN FAILED!")
        print(f"Error Code: {error_code}")
        print(f"Error Message: {error_msg}")
        
        # Interpret error codes
        if error_code == -6:
            print("\n🔍 DIAGNOSIS: AUTHORIZATION FAILED")
            print("This typically means:")
            print("  • Account has expired ❌")
            print("  • Wrong password ❌")
            print("  • Account disabled by broker ❌")
            print("  • Server connection issue ❌")
            
        elif error_code == -5:
            print("\n🔍 DIAGNOSIS: CONNECTION FAILED")
            print("This typically means:")
            print("  • Server is offline ❌")
            print("  • Network connectivity issue ❌")
            print("  • Firewall blocking connection ❌")
            
        elif error_code == -10004:
            print("\n🔍 DIAGNOSIS: INVALID ACCOUNT")
            print("This means:")
            print("  • Account definitely expired/deleted ❌")
            
        elif error_code == -1:
            print("\n🔍 DIAGNOSIS: GENERAL ERROR")
            print("This could mean:")
            print("  • MT5 not installed properly ❌")
            print("  • Path incorrect ❌")
            
        print(f"\n🎯 CONCLUSION: Account {mt5_login} appears to be EXPIRED or INVALID")
        return False
    
    print("✅ LOGIN SUCCESSFUL!")
    
    # Test 2: Get account information
    print("\nTEST 2: Account Information")
    print("-" * 30)
    
    account_info = mt5.account_info()
    if account_info:
        print(f"✅ Account Details Retrieved:")
        print(f"  Login: {account_info.login}")
        print(f"  Name: {account_info.name}")
        print(f"  Server: {account_info.server}")
        print(f"  Company: {account_info.company}")
        print(f"  Currency: {account_info.currency}")
        print(f"  Balance: ${account_info.balance:.2f}")
        print(f"  Equity: ${account_info.equity:.2f}")
        print(f"  Margin: ${account_info.margin:.2f}")
        print(f"  Trading Allowed: {account_info.trade_allowed}")
        print(f"  Expert Trading: {account_info.trade_expert}")
        
        # Check trading permissions
        if not account_info.trade_allowed:
            print("  ⚠️ WARNING: Trading is disabled on this account")
        if not account_info.trade_expert:
            print("  ⚠️ WARNING: Expert Advisor trading is disabled")
            
    else:
        print("❌ Could not retrieve account information")
        print("This suggests account issues even if login succeeded")
    
    # Test 3: Market data access
    print("\nTEST 3: Market Data Access")
    print("-" * 30)
    
    symbols_to_test = ["XAUUSD", "EURUSD", "GBPUSD"]
    data_working = False
    
    for symbol in symbols_to_test:
        print(f"\nTesting {symbol}:")
        
        # Test tick data
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            # Provide both MT5/UTC and local representations
            tick_time_utc = datetime.utcfromtimestamp(tick.time)
            tick_time_local = datetime.fromtimestamp(tick.time)
            age_seconds = (datetime.utcnow() - tick_time_utc).total_seconds()

            print(f"  ✅ Tick Data: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
            print(f"  📅 Tick Time (MT5/UTC): {tick_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  📅 Tick Time (Local): {tick_time_local.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  ⏰ Data Age: {age_seconds:.0f} seconds")

            if age_seconds < 300:  # Less than 5 minutes
                print(f"  ✅ Data is FRESH")
                data_working = True
            else:
                print(f"  ❌ Data is OLD (Age: {age_seconds/3600:.1f} hours)")
                
        else:
            print(f"  ❌ No tick data available")
        
        # Test historical data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 5)
        if rates:
            latest_bar_time_utc = datetime.utcfromtimestamp(rates[-1]['time'])
            latest_bar_time_local = datetime.fromtimestamp(rates[-1]['time'])
            bar_age = (datetime.utcnow() - latest_bar_time_utc).total_seconds()

            print(f"  📊 Latest Bar (MT5/UTC): {latest_bar_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"  📊 Latest Bar (Local): {latest_bar_time_local.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  📊 Bar Age: {bar_age:.0f} seconds")
            print(f"  📊 Close Price: {rates[-1]['close']:.5f}")

            if bar_age < 1800:  # Less than 30 minutes
                print(f"  ✅ Historical data is current")
            else:
                print(f"  ❌ Historical data is old")
        else:
            print(f"  ❌ No historical data available")
    
    # Test 4: Symbol information
    print(f"\nTEST 4: Symbol Information")
    print("-" * 30)
    
    symbol_info = mt5.symbol_info("XAUUSD")
    if symbol_info:
        print(f"✅ Symbol info available:")
        print(f"  Spread: {symbol_info.spread}")
        print(f"  Digits: {symbol_info.digits}")
        print(f"  Point: {symbol_info.point}")
        print(f"  Trade Mode: {symbol_info.trade_mode}")
    else:
        print(f"❌ No symbol information available")
    
    # Final conclusion
    print("\n" + "=" * 60)
    print("🎯 FINAL DIAGNOSIS")
    print("=" * 60)
    
    if account_info and data_working:
        print("✅ ACCOUNT STATUS: ACTIVE AND WORKING")
        print("Your account is NOT expired.")
        print("The issue is likely with data feed or MT5 settings.")
        print("\nRecommended actions:")
        print("  1. Check MT5 chart refresh (F5)")
        print("  2. Check internet connection")
        print("  3. Restart MT5 application")
        print("  4. Check Windows firewall settings")
        
    elif account_info and not data_working:
        print("⚠️ ACCOUNT STATUS: ACTIVE BUT DATA ISSUES")
        print("Account login works but market data is problematic.")
        print("This suggests server or connectivity issues.")
        print("\nRecommended actions:")
        print("  1. Try different OctaFX server")
        print("  2. Check network connectivity")
        print("  3. Contact OctaFX support")
        
    else:
        print("❌ ACCOUNT STATUS: EXPIRED OR INVALID")
        print("Account cannot be accessed or has serious issues.")
        print("\nRecommended actions:")
        print("  1. Create new demo account")
        print("  2. Contact OctaFX support")
        print("  3. Try different broker")
    
    mt5.shutdown()
    return account_info is not None and data_working

if __name__ == "__main__":
    verify_account_expiration()