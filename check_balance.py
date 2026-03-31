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
    account = mt5.account_info()
    if account:
        print(f"Account Balance: ${account.balance:.2f}")
        print(f"Account Equity: ${account.equity:.2f}")
        print(f"Free Margin: ${account.margin_free:.2f}")
        print(f"Margin Level: {account.margin_level:.2f}%")
    
    # Check positions
    positions = mt5.positions_get()
    if positions:
        print(f"\nOpen Positions: {len(positions)}")
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"  {pos.symbol}: {pos_type} {pos.volume} lots | P&L: ${pos.profit:.2f}")
    else:
        print("\nNo open positions")
    
    mt5.shutdown()
else:
    print("MT5 connection failed")