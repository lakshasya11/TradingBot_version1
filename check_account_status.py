import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

def check_account_status():
    """Check if MT5 account is expired or has issues"""
    load_dotenv()
    
    # Get credentials
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    mt5_path = os.getenv("MT5_PATH")
    
    print("=== MT5 ACCOUNT STATUS CHECK ===")
    print(f"Login: {mt5_login}")
    print(f"Server: {mt5_server}")
    print(f"Path: {mt5_path}")
    print("-" * 40)
    
    # Try to initialize with credentials
    print("Testing connection with credentials...")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        error_code, error_msg = mt5.last_error()
        print(f"❌ CONNECTION FAILED!")
        print(f"Error Code: {error_code}")
        print(f"Error Message: {error_msg}")
        
        # Interpret common error codes
        if error_code == -6:
            print("\n🔍 DIAGNOSIS: Authorization Failed")
            print("Possible causes:")
            print("- Account expired")
            print("- Wrong password")
            print("- Account disabled")
            print("- Server changed")
            
        elif error_code == -5:
            print("\n🔍 DIAGNOSIS: Connection Failed")
            print("Possible causes:")
            print("- Server offline")
            print("- Internet connection issue")
            print("- Firewall blocking")
            
        elif error_code == -10004:
            print("\n🔍 DIAGNOSIS: Invalid Account")
            print("Account likely expired or deleted")
            
        return False
    
    # If connection successful, get account info
    print("✅ CONNECTION SUCCESSFUL!")
    
    account_info = mt5.account_info()
    if account_info:
        print("\n📊 ACCOUNT DETAILS:")
        print(f"Login: {account_info.login}")
        print(f"Server: {account_info.server}")
        print(f"Name: {account_info.name}")
        print(f"Company: {account_info.company}")
        print(f"Currency: {account_info.currency}")
        print(f"Balance: {account_info.balance}")
        print(f"Equity: {account_info.equity}")
        print(f"Margin: {account_info.margin}")
        print(f"Trade Allowed: {account_info.trade_allowed}")
        print(f"Trade Expert: {account_info.trade_expert}")
        
        # Check if trading is allowed
        if not account_info.trade_allowed:
            print("\n⚠️ WARNING: Trading not allowed on this account")
        
        if not account_info.trade_expert:
            print("\n⚠️ WARNING: Expert Advisor trading disabled")
            
    else:
        print("❌ Could not retrieve account information")
    
    # Test data access
    print("\n📈 TESTING DATA ACCESS:")
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1)
    if rates is not None:
        print("✅ Market data access working")
    else:
        print("❌ Market data access failed")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    check_account_status()