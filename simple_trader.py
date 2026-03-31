import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv

def simple_live_trader():
    """Minimal live trading system"""
    load_dotenv()
    
    # Initialize MT5
    if not mt5.initialize(path=os.getenv("MT5_PATH"), 
                         login=int(os.getenv("MT5_LOGIN")), 
                         password=os.getenv("MT5_PASSWORD"), 
                         server=os.getenv("MT5_SERVER")):
        print("MT5 initialization failed")
        return
    
    # Safety check
    account = mt5.account_info()
    if account and account.trade_mode != 0:
        print("LIVE ACCOUNT DETECTED!")
        confirm = input("Type 'LIVE' to confirm: ")
        if confirm != 'LIVE':
            print("Trading cancelled")
            return
    
    print("Live Trading System Started")
    print("Press Ctrl+C to stop")
    
    symbol = "XAUUSD"
    tick_count = 0
    
    try:
        while True:
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print("No tick data")
                time.sleep(1)
                continue
            
            # Get rates for analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
            if rates is None or len(rates) < 50:
                print("No rate data")
                time.sleep(1)
                continue
            
            df = pd.DataFrame(rates)
            
            # Simple RSI calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Simple EMA calculation
            ema9 = df['close'].ewm(span=9).mean().iloc[-1]
            ema21 = df['close'].ewm(span=21).mean().iloc[-1]
            
            # Simple ATR calculation
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1]
            
            current_price = (tick.bid + tick.ask) / 2
            
            # Trading logic
            buy_signal = current_rsi > 45 and ema9 > ema21
            sell_signal = current_rsi < 55 and ema9 < ema21
            
            if buy_signal or sell_signal:
                tick_count += 1
                signal = "BUY" if buy_signal else "SELL"
                
                print(f"\nSignal #{tick_count}: {signal}")
                print(f"Price: {current_price:.2f} | RSI: {current_rsi:.1f}")
                print(f"EMA9: {ema9:.2f} | EMA21: {ema21:.2f} | ATR: {atr:.2f}")
                
                # Calculate order parameters
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    tick_size = symbol_info.trade_tick_size
                    min_volume = symbol_info.volume_min
                    
                    if signal == "BUY":
                        entry_price = tick.ask + tick_size
                        stop_loss = current_price - (atr * 1.1)
                        take_profit = current_price + (atr * 1.1 * 2.0)
                        order_type = mt5.ORDER_TYPE_BUY
                    else:
                        entry_price = tick.bid - tick_size
                        stop_loss = current_price + (atr * 1.1)
                        take_profit = current_price - (atr * 1.1 * 2.0)
                        order_type = mt5.ORDER_TYPE_SELL
                    
                    # Use minimum volume for safety
                    volume = min_volume
                    
                    print(f"Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                    print(f"Volume: {volume}")
                    
                    # Place order
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type,
                        "price": entry_price,
                        "sl": stop_loss,
                        "tp": take_profit,
                        "comment": "LiveBot",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                        "magic": 123456
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"SUCCESS: Ticket #{result.order} | Fill: {result.price:.5f}")
                    else:
                        error_msg = result.comment if result else "Unknown error"
                        error_code = result.retcode if result else "N/A"
                        print(f"FAILED: {error_msg} (Code: {error_code})")
                
                # Wait 30 seconds before next signal
                time.sleep(30)
            else:
                # Check every 5 seconds
                time.sleep(5)
                
    except KeyboardInterrupt:
        print(f"\nTrading stopped. Total signals: {tick_count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    simple_live_trader()