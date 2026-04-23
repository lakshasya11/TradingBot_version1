"""
MT5 Connection Module - Consolidated Connection Management
Eliminates duplicate MT5 initialization code across files
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

class MT5Connection:
    """MT5 connection management utilities"""
    
    @staticmethod
    def initialize_mt5():
        """Initialize MT5 connection using environment variables"""
        load_dotenv()
        
        mt5_path = os.getenv("MT5_PATH")
        mt5_login = os.getenv("MT5_LOGIN")
        mt5_pass = os.getenv("MT5_PASSWORD")
        mt5_server = os.getenv("MT5_SERVER")
        
        if not all([mt5_path, mt5_login, mt5_pass, mt5_server]):
            print("❌ CRITICAL: .env file is missing MT5 credentials.")
            return False
        
        try:
            mt5_login = int(mt5_login)
        except ValueError:
            print("❌ CRITICAL: MT5_LOGIN must be a valid integer.")
            return False
        
        if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
            print(f"❌ MT5 initialization failed: {mt5.last_error()}")
            return False
        
        print("✅ MT5 connection established successfully.")
        return True
    
    @staticmethod
    def check_connection():
        """Check if MT5 connection is active"""
        if not mt5.terminal_info():
            print("⚠️ MT5 connection lost, attempting to reconnect...")
            return MT5Connection.initialize_mt5()
        return True
    
    @staticmethod
    def shutdown():
        """Safely shutdown MT5 connection"""
        mt5.shutdown()
        print("✅ MT5 connection terminated.")
    
    @staticmethod
    def get_symbol_info(symbol: str):
        """Get symbol information with error handling"""
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"❌ Failed to get symbol info for {symbol}")
            return None
        return symbol_info
    
    @staticmethod
    def get_tick(symbol: str):
        """Get current tick with error handling"""
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"❌ Failed to get tick data for {symbol}")
            return None
        return tick
    
    @staticmethod
    def fetch_rates(symbol: str, timeframe, bars: int = 100):
        """Fetch OHLCV rates with error handling"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            print(f"❌ Failed to fetch rates for {symbol}")
            return None
        return rates