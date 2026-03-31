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
    # Check XAUUSD availability
    symbol_info = mt5.symbol_info("XAUUSD")
    if symbol_info:
        print(f"XAUUSD Symbol Info:")
        print(f"  Available: {symbol_info.visible}")
        print(f"  Tradeable: {symbol_info.trade_mode}")
        print(f"  Min Volume: {symbol_info.volume_min}")
        print(f"  Max Volume: {symbol_info.volume_max}")
        print(f"  Volume Step: {symbol_info.volume_step}")
        
        # Check current tick
        tick = mt5.symbol_info_tick("XAUUSD")
        if tick:
            print(f"  Current Bid: {tick.bid}")
            print(f"  Current Ask: {tick.ask}")
            print(f"  Last Update: {tick.time}")
        else:
            print("  No tick data available")
    else:
        print("XAUUSD not found on this server")
        
        # Show available symbols
        symbols = mt5.symbols_get()
        gold_symbols = [s.name for s in symbols if 'XAU' in s.name or 'GOLD' in s.name]
        print(f"Available Gold symbols: {gold_symbols}")
    
    mt5.shutdown()
else:
    print("MT5 connection failed")