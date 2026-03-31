import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

def test_order_execution():
    """Test basic order execution to identify the problem"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("🔍 ORDER EXECUTION DIAGNOSTIC")
    print("=" * 50)
    
    # Check account info
    account_info = mt5.account_info()
    if account_info:
        print(f"Account: {account_info.login}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Equity: ${account_info.equity:.2f}")
        print(f"Margin Free: ${account_info.margin_free:.2f}")
        print(f"Trade Allowed: {account_info.trade_allowed}")
        print(f"Trade Expert: {account_info.trade_expert}")
    else:
        print("❌ Cannot get account info")
        return
    
    # Check symbol info
    symbol = "XAUUSD"
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f"\nSymbol: {symbol}")
        print(f"Trade Mode: {symbol_info.trade_mode}")
        print(f"Min Volume: {symbol_info.volume_min}")
        print(f"Max Volume: {symbol_info.volume_max}")
        print(f"Volume Step: {symbol_info.volume_step}")
        print(f"Digits: {symbol_info.digits}")
        print(f"Spread: {symbol_info.spread}")
    else:
        print(f"❌ Cannot get {symbol} info")
        return
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"\nCurrent Price:")
        print(f"Bid: {tick.bid:.5f}")
        print(f"Ask: {tick.ask:.5f}")
        print(f"Spread: {tick.ask - tick.bid:.5f}")
    else:
        print("❌ Cannot get tick data")
        return
    
    # Test a simple SELL order
    print(f"\n🧪 TESTING SIMPLE SELL ORDER")
    print("-" * 30)
    
    volume = symbol_info.volume_min  # Use minimum volume
    price = tick.bid
    
    # Calculate stop loss and take profit (simple 50 point distance)
    point = symbol_info.point
    stop_loss = price + (50 * point)  # 50 points above for SELL
    take_profit = price - (100 * point)  # 100 points below for SELL
    
    print(f"Volume: {volume}")
    print(f"Entry Price: {price:.5f}")
    print(f"Stop Loss: {stop_loss:.5f}")
    print(f"Take Profit: {take_profit:.5f}")
    
    # Create order request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "magic": 123456,
        "comment": "Test_Order",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    print(f"\nOrder Request:")
    for key, value in request.items():
        print(f"  {key}: {value}")
    
    # Send order
    print(f"\n📤 Sending order...")
    result = mt5.order_send(request)
    
    if result:
        print(f"\nOrder Result:")
        print(f"  Return Code: {result.retcode}")
        print(f"  Comment: {result.comment}")
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ ORDER SUCCESSFUL!")
            print(f"  Order Ticket: {result.order}")
            print(f"  Deal Ticket: {result.deal}")
            print(f"  Volume: {result.volume}")
            print(f"  Price: {result.price}")
        else:
            print(f"❌ ORDER FAILED!")
            print(f"  Error Code: {result.retcode}")
            print(f"  Error Message: {result.comment}")
            
            # Common error explanations
            error_codes = {
                10004: "Requote - price changed",
                10006: "Request rejected",
                10007: "Request canceled by trader", 
                10008: "Order placed",
                10009: "Request completed",
                10010: "Only part of request completed",
                10011: "Request processing error",
                10012: "Request canceled by timeout",
                10013: "Invalid request",
                10014: "Invalid volume",
                10015: "Invalid price",
                10016: "Invalid stops",
                10017: "Trade disabled",
                10018: "Market closed",
                10019: "No money",
                10020: "Price changed",
                10021: "Off quotes",
                10022: "Invalid expiration",
                10023: "Order state changed",
                10024: "Too frequent requests",
                10025: "No changes in request",
                10026: "Autotrading disabled",
                10027: "Market closed",
                10028: "Invalid volume",
                10029: "Invalid price",
                10030: "Invalid stops"
            }
            
            if result.retcode in error_codes:
                print(f"  Explanation: {error_codes[result.retcode]}")
    else:
        print("❌ No result returned from order_send")
    
    # Check if there are any open positions
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        print(f"\n📊 Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  Ticket: {pos.ticket} | Type: {'BUY' if pos.type == 0 else 'SELL'} | Volume: {pos.volume} | Price: {pos.price_open}")
    else:
        print(f"\n📊 No open positions for {symbol}")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_order_execution()