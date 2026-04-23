import MetaTrader5 as mt5
import time
from mt5_chart_lines import MT5ChartLines
from dotenv import load_dotenv
import os

def test_mt5_lines():
    """Test MT5 line drawing functionality"""
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    symbol = "XAUUSD"
    
    print("🧪 TESTING MT5 LINE DRAWING")
    print("=" * 40)
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print("❌ Failed to get tick data")
        return
    
    current_price = tick.bid
    print(f"Current price: {current_price:.2f}")
    
    # Test drawing lines
    test_sl = current_price - 2.0
    test_tp = current_price + 3.0
    test_trail = current_price - 1.5
    
    print(f"Drawing test lines:")
    print(f"  Stop Loss: {test_sl:.2f}")
    print(f"  Take Profit: {test_tp:.2f}")
    print(f"  Trailing: {test_trail:.2f}")
    
    # Draw test lines
    success1 = MT5ChartLines.draw_horizontal_line(
        symbol, test_sl, "TEST_SL", 0x0000FF, f"🔴 TEST STOP LOSS: {test_sl:.2f}"
    )
    
    success2 = MT5ChartLines.draw_horizontal_line(
        symbol, test_tp, "TEST_TP", 0x00FF00, f"🟢 TEST TAKE PROFIT: {test_tp:.2f}"
    )
    
    success3 = MT5ChartLines.draw_horizontal_line(
        symbol, test_trail, "TEST_TRAIL", 0x0080FF, f"🟠 TEST TRAILING: {test_trail:.2f}"
    )
    
    if success1 and success2 and success3:
        print("✅ All test lines drawn successfully!")
        print("Check your MT5 chart - you should see 3 dotted lines")
    else:
        print("❌ Some lines failed to draw")
    
    # Keep lines visible for 10 seconds
    print("Lines will be visible for 10 seconds...")
    time.sleep(10)
    
    # Clear test lines
    mt5.object_delete(symbol, "TEST_SL")
    mt5.object_delete(symbol, "TEST_TP")
    mt5.object_delete(symbol, "TEST_TRAIL")
    print("Test lines cleared")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_mt5_lines()