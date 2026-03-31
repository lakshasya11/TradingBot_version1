import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize MT5
mt5_path = os.getenv("MT5_PATH")
mt5_login = int(os.getenv("MT5_LOGIN"))
mt5_pass = os.getenv("MT5_PASSWORD")
mt5_server = os.getenv("MT5_SERVER")

if mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
    # Get all open positions
    positions = mt5.positions_get()
    
    if positions:
        print(f"Found {len(positions)} open positions. Closing all...")
        
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            
            # Close position
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "comment": "Close all positions",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(close_request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Closed {pos_type} {pos.volume} lots on {pos.symbol} | P&L: ${pos.profit:.2f}")
            else:
                error = result.comment if result else "Unknown error"
                print(f"❌ Failed to close position: {error}")
        
        # Check account after closing
        account = mt5.account_info()
        if account:
            print(f"\nAccount after closing:")
            print(f"Balance: ${account.balance:.2f}")
            print(f"Free Margin: ${account.margin_free:.2f}")
    else:
        print("No open positions found")
    
    mt5.shutdown()
else:
    print("MT5 connection failed")