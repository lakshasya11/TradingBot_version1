import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

def test_mt5_connection():
    load_dotenv()
    
    # Get credentials
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    print(f"Testing MT5 connection...")
    print(f"Login: {mt5_login}")
    print(f"Server: {mt5_server}")
    print(f"Path: {mt5_path}")
    
    # Test 1: Initialize without credentials
    if not mt5.initialize():
        print(f"Basic initialization failed: {mt5.last_error()}")
        return False
    
    # Test 2: Login with credentials
    if not mt5.login(mt5_login, mt5_pass, mt5_server):
        print(f"Login failed: {mt5.last_error()}")
        print("Possible issues:")
        print("1. Wrong login/password")
        print("2. Wrong server name")
        print("3. Account expired/disabled")
        print("4. MT5 terminal not running")
        mt5.shutdown()
        return False
    
    # Test 3: Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"Connection successful!")
        print(f"Account: {account_info.login}")
        print(f"Balance: ${account_info.balance}")
        print(f"Server: {account_info.server}")
    else:
        print(f"Account info failed: {mt5.last_error()}")
    
    mt5.shutdown()
    return True

if __name__ == "__main__":
    test_mt5_connection()