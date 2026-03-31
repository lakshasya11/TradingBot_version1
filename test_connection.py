import MetaTrader5 as mt5

def test_connection():
    print("Testing MT5 connection...")
    
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return False
    
    print("✅ MT5 initialized successfully")
    
    # Test login
    login = 5044214016
    password = "Tq-w6rPx"
    server = "MetaQuotes-Demo"
    
    print(f"Attempting login: {login} @ {server}")
    
    if not mt5.login(login, password, server):
        print(f"❌ Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print("✅ Login successful!")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"Account: {account_info.name}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Equity: ${account_info.equity:.2f}")
    
    # Test symbol
    symbol = "EURUSD"
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"✅ {symbol} - Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
    else:
        print(f"❌ Cannot get {symbol} data")
    
    mt5.shutdown()
    print("✅ Connection test completed")
    return True

if __name__ == "__main__":
    test_connection()