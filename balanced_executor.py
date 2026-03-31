import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

def balanced_trade_executor():
    """Execute trades with auto-balanced parameters for broker acceptance"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return
    
    def get_balanced_order_params(symbol, order_type):
        """Calculate broker-compliant order parameters"""
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not symbol_info or not tick:
            return None
        
        # Use minimum volume (safest)
        volume = symbol_info.volume_min
        
        # Get current prices
        if order_type == "SELL":
            entry_price = tick.bid
        else:  # BUY
            entry_price = tick.ask
        
        # Calculate minimum stop distance (broker requirement)
        min_stop_level = symbol_info.trade_stops_level * symbol_info.point
        spread = (tick.ask - tick.bid)
        
        # Use larger of: minimum stop level or 3x spread (safer)
        safe_stop_distance = max(min_stop_level, spread * 3)
        
        # Calculate stop loss and take profit
        if order_type == "SELL":
            stop_loss = entry_price + safe_stop_distance
            take_profit = entry_price - (safe_stop_distance * 2)  # 2:1 RR
        else:  # BUY
            stop_loss = entry_price - safe_stop_distance
            take_profit = entry_price + (safe_stop_distance * 2)  # 2:1 RR
        
        # Round to symbol digits
        digits = symbol_info.digits
        entry_price = round(entry_price, digits)
        stop_loss = round(stop_loss, digits)
        take_profit = round(take_profit, digits)
        
        return {
            'volume': volume,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'min_stop_distance': safe_stop_distance,
            'spread': spread
        }
    
    def execute_balanced_trade(symbol, order_type):
        """Execute trade with balanced parameters"""
        
        print(f"\n🎯 EXECUTING BALANCED {order_type} TRADE")
        print("=" * 40)
        
        # Get balanced parameters
        params = get_balanced_order_params(symbol, order_type)
        if not params:
            print("❌ Cannot get symbol parameters")
            return False
        
        print(f"Symbol: {symbol}")
        print(f"Volume: {params['volume']}")
        print(f"Entry: {params['entry_price']:.5f}")
        print(f"Stop Loss: {params['stop_loss']:.5f}")
        print(f"Take Profit: {params['take_profit']:.5f}")
        print(f"Stop Distance: {params['min_stop_distance']:.5f}")
        print(f"Spread: {params['spread']:.5f}")
        
        # Create order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": params['volume'],
            "type": mt5.ORDER_TYPE_SELL if order_type == "SELL" else mt5.ORDER_TYPE_BUY,
            "price": params['entry_price'],
            "sl": params['stop_loss'],
            "tp": params['take_profit'],
            "magic": 123456,
            "comment": f"Balanced_{order_type}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Execute order
        print(f"\n📤 Sending balanced order...")
        result = mt5.order_send(request)
        
        if result:
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ TRADE EXECUTED SUCCESSFULLY!")
                print(f"   Ticket: {result.order}")
                print(f"   Deal: {result.deal}")
                print(f"   Volume: {result.volume}")
                print(f"   Price: {result.price:.5f}")
                return True
            else:
                print(f"❌ Trade failed: {result.comment} (Code: {result.retcode})")
                
                # Try with even safer parameters if failed
                if result.retcode in [10016, 10030]:  # Invalid stops
                    print("🔄 Retrying with safer stop distances...")
                    return retry_with_safer_stops(symbol, order_type, params)
                
                return False
        else:
            print("❌ No result from order_send")
            return False
    
    def retry_with_safer_stops(symbol, order_type, original_params):
        """Retry with even safer stop loss distances"""
        
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        # Use 5x the minimum stop level (very safe)
        min_stop_level = symbol_info.trade_stops_level * symbol_info.point
        safer_distance = min_stop_level * 5
        
        entry_price = original_params['entry_price']
        
        if order_type == "SELL":
            stop_loss = entry_price + safer_distance
            take_profit = entry_price - (safer_distance * 1.5)  # Smaller RR for safety
        else:  # BUY
            stop_loss = entry_price - safer_distance
            take_profit = entry_price + (safer_distance * 1.5)
        
        # Round to digits
        digits = symbol_info.digits
        stop_loss = round(stop_loss, digits)
        take_profit = round(take_profit, digits)
        
        print(f"Safer Stop Loss: {stop_loss:.5f}")
        print(f"Safer Take Profit: {take_profit:.5f}")
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": original_params['volume'],
            "type": mt5.ORDER_TYPE_SELL if order_type == "SELL" else mt5.ORDER_TYPE_BUY,
            "price": entry_price,
            "sl": stop_loss,
            "tp": take_profit,
            "magic": 123456,
            "comment": f"SafeBalanced_{order_type}",
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ SAFER TRADE EXECUTED!")
            print(f"   Ticket: {result.order}")
            return True
        else:
            error_msg = result.comment if result else "Unknown error"
            print(f"❌ Even safer trade failed: {error_msg}")
            return False
    
    # Main execution
    print("⚖️ BALANCED TRADE EXECUTOR")
    print("=" * 50)
    
    # Check account
    account_info = mt5.account_info()
    if account_info:
        print(f"Account: {account_info.login}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Free Margin: ${account_info.margin_free:.2f}")
        
        if account_info.balance < 100:
            print("⚠️ Low balance - using minimum volume")
        
        if not account_info.trade_allowed:
            print("❌ Trading not allowed on this account")
            mt5.shutdown()
            return
    
    # Execute a balanced SELL trade (based on your earlier signals)
    symbol = "XAUUSD"
    success = execute_balanced_trade(symbol, "SELL")
    
    if success:
        print(f"\n🎉 BALANCED TRADE SUCCESSFUL!")
        
        # Show open positions
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            print(f"\n📊 Open Positions:")
            for pos in positions:
                pnl = pos.profit
                print(f"   Ticket: {pos.ticket} | P&L: ${pnl:.2f}")
    else:
        print(f"\n😞 Could not execute balanced trade")
        print("   This might be due to:")
        print("   - Market closed")
        print("   - Insufficient funds") 
        print("   - Symbol not available")
        print("   - Account restrictions")
    
    mt5.shutdown()

if __name__ == "__main__":
    balanced_trade_executor()