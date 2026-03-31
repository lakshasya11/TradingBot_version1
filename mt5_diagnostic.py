import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

def diagnose_mt5_connection():
    """Comprehensive MT5 diagnostic check"""
    
    load_dotenv()
    
    print("🔍 MT5 DIAGNOSTIC CHECK")
    print("=" * 50)
    
    # 1. Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    print(f"1. Connecting to MT5...")
    print(f"   Login: {mt5_login}")
    print(f"   Server: {mt5_server}")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("✅ MT5 connection successful")
    
    # 2. Check account info
    account_info = mt5.account_info()
    if account_info:
        print(f"\n2. Account Information:")
        print(f"   Balance: ${account_info.balance:.2f}")
        print(f"   Equity: ${account_info.equity:.2f}")
        print(f"   Free Margin: ${account_info.margin_free:.2f}")
        print(f"   Trade Mode: {account_info.trade_mode} (0=Demo, 1=Contest, 2=Real)")
        print(f"   Trade Allowed: {'✅ YES' if account_info.trade_allowed else '❌ NO'}")
        print(f"   Trade Expert: {'✅ YES' if account_info.trade_expert else '❌ NO'}")
    else:
        print("❌ Could not get account info")
    
    # 3. Check symbol info
    symbol = "XAUUSD"
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f"\n3. Symbol Information ({symbol}):")
        print(f"   Visible: {'✅ YES' if symbol_info.visible else '❌ NO'}")
        print(f"   Trade Mode: {symbol_info.trade_mode}")
        print(f"   Min Volume: {symbol_info.volume_min}")
        print(f"   Max Volume: {symbol_info.volume_max}")
        print(f"   Volume Step: {symbol_info.volume_step}")
        print(f"   Margin Required: ${symbol_info.margin_initial:.2f}")
    else:
        print(f"❌ Could not get {symbol} info")
    
    # 4. Check current tick
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"\n4. Live Market Data:")
        print(f"   BID: {tick.bid:.5f}")
        print(f"   ASK: {tick.ask:.5f}")
        print(f"   Spread: {tick.ask - tick.bid:.5f}")
        print(f"   Time: {tick.time}")
    else:
        print("❌ Could not get live tick data")
    
    # 5. Check existing positions
    positions = mt5.positions_get(symbol=symbol)
    print(f"\n5. Current Positions:")
    if positions:
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"   Ticket #{pos.ticket}: {pos_type} {pos.volume} lots at {pos.price_open} | P&L: ${pos.profit:.2f}")
    else:
        print("   No open positions")
    
    # 6. Test a small order (0.01 lots)
    print(f"\n6. Testing Order Placement...")
    
    if tick and symbol_info and account_info.trade_allowed:
        # Try a small BUY order
        test_request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': 0.01,
            'type': mt5.ORDER_TYPE_BUY,
            'price': tick.ask,
            'sl': tick.ask - 2.0,  # $2 stop loss
            'tp': tick.ask + 4.0,  # $4 take profit
            'comment': 'MT5 Diagnostic Test',
            'type_filling': mt5.ORDER_FILLING_IOC,
            'magic': 999999,
            'deviation': 0
        }
        
        print(f"   Sending test BUY order...")
        print(f"   Price: {tick.ask:.5f}")
        print(f"   Volume: 0.01 lots")
        print(f"   Required Margin: ~${symbol_info.margin_initial * 0.01:.2f}")
        
        result = mt5.order_send(test_request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ TEST ORDER SUCCESSFUL!")
            print(f"   Ticket: #{result.order}")
            print(f"   Filled at: {result.price:.5f}")
            
            # Immediately close the test position
            close_request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': 0.01,
                'type': mt5.ORDER_TYPE_SELL,
                'position': result.order,
                'price': tick.bid,
                'comment': 'Close diagnostic test',
                'type_filling': mt5.ORDER_FILLING_IOC,
                'magic': 999999
            }
            
            close_result = mt5.order_send(close_request)
            if close_result and close_result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Test position closed successfully")
            else:
                print(f"⚠️ Could not close test position - please close manually")
                
        else:
            error_msg = result.comment if result else "Unknown error"
            retcode = result.retcode if result else "No result"
            print(f"❌ TEST ORDER FAILED!")
            print(f"   Error: {error_msg}")
            print(f"   RetCode: {retcode}")
            
            # Common error explanations
            if result:
                if result.retcode == 10019:
                    print(f"   → Insufficient funds (need ~${symbol_info.margin_initial * 0.01:.2f})")
                elif result.retcode == 10027:
                    print(f"   → AutoTrading disabled in MT5")
                elif result.retcode == 10018:
                    print(f"   → Market is closed")
                elif result.retcode == 10016:
                    print(f"   → Invalid volume")
    else:
        print("❌ Cannot test order - missing data or trading not allowed")
    
    print(f"\n" + "=" * 50)
    print("🔍 DIAGNOSTIC COMPLETE")
    
    mt5.shutdown()

if __name__ == "__main__":
    diagnose_mt5_connection()