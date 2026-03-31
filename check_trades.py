import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

# Initialize MT5
mt5_path = os.getenv("MT5_PATH")
mt5_login = int(os.getenv("MT5_LOGIN"))
mt5_pass = os.getenv("MT5_PASSWORD")
mt5_server = os.getenv("MT5_SERVER")

if mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
    print(f"Connected to Account: {mt5_login} on {mt5_server}")
    
    # Check current positions
    positions = mt5.positions_get()
    if positions:
        print(f"\n=== CURRENT POSITIONS ({len(positions)}) ===")
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            print(f"Ticket: {pos.ticket}")
            print(f"  Type: {pos_type}")
            print(f"  Symbol: {pos.symbol}")
            print(f"  Volume: {pos.volume}")
            print(f"  Open Price: {pos.price_open}")
            print(f"  Current Price: {pos.price_current}")
            print(f"  P&L: ${pos.profit:.2f}")
            print(f"  Magic: {pos.magic}")
            print(f"  Comment: {pos.comment}")
            print("-" * 40)
    else:
        print("\n=== NO CURRENT POSITIONS ===")
    
    # Check recent trade history
    now = datetime.now()
    from_date = now - timedelta(days=7)  # Last 7 days
    
    deals = mt5.history_deals_get(from_date, now)
    if deals:
        print(f"\n=== RECENT DEALS (Last 7 days) ===")
        for deal in deals[-10:]:  # Show last 10 deals
            deal_type = "BUY" if deal.type == 0 else "SELL"
            print(f"Ticket: {deal.ticket}")
            print(f"  Time: {datetime.fromtimestamp(deal.time)}")
            print(f"  Type: {deal_type}")
            print(f"  Symbol: {deal.symbol}")
            print(f"  Volume: {deal.volume}")
            print(f"  Price: {deal.price}")
            print(f"  Profit: ${deal.profit:.2f}")
            print(f"  Magic: {deal.magic}")
            print(f"  Comment: {deal.comment}")
            print("-" * 40)
    else:
        print("\n=== NO RECENT DEALS ===")
    
    mt5.shutdown()
else:
    print("MT5 connection failed")