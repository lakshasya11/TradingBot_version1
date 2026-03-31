import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy

def balanced_trading_system():
    """Balanced conditions - not too strict, not too loose"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    
    print("⚖️ BALANCED TRADING SYSTEM")
    print("=" * 50)
    print("Reasonable conditions that should execute trades:")
    print("BUY: RSI>45 + EMA9>EMA21")
    print("SELL: RSI<55 + EMA9<EMA21") 
    print("(Removed Supertrend requirement)")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    trades_executed = 0
    
    try:
        while True:
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) > 0 and tick:
                analysis = strategy.analyze_timeframe("M1")
                
                if analysis:
                    rsi = analysis.get('rsi', 50)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    atr = analysis.get('atr', 0)
                    current_price = tick.bid
                    
                    # UTC time
                    utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                    time_display = utc_time.strftime("%H:%M:%S")
                    
                    # BALANCED CONDITIONS (More reasonable)
                    buy_conditions = rsi > 45 and ema9 > ema21
                    sell_conditions = rsi < 55 and ema9 < ema21
                    
                    signal = "NONE"
                    if buy_conditions and not sell_conditions:
                        signal = "BUY"
                    elif sell_conditions and not buy_conditions:
                        signal = "SELL"
                    
                    print(f"\n[{time_display} UTC] Price: {current_price:.2f}")
                    print(f"RSI: {rsi:.1f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f}")
                    print(f"BUY: RSI>45={rsi>45} + EMA9>EMA21={ema9>ema21} = {buy_conditions}")
                    print(f"SELL: RSI<55={rsi<55} + EMA9<EMA21={ema9<ema21} = {sell_conditions}")
                    print(f"SIGNAL: {signal}")
                    
                    if signal != "NONE":
                        print(f"🎆 EXECUTING {signal} TRADE!")
                        
                        # Calculate trade parameters
                        if signal == "BUY":
                            entry_price = tick.ask
                            stop_loss = current_price - (atr * 1.5)
                            take_profit = current_price + (atr * 3.0)  # 2:1 RR
                        else:  # SELL
                            entry_price = tick.bid
                            stop_loss = current_price + (atr * 1.5)
                            take_profit = current_price - (atr * 3.0)  # 2:1 RR
                        
                        # Calculate position size
                        position_size = strategy.calculate_position_size(entry_price, stop_loss, 100)
                        
                        print(f"Entry: {entry_price:.5f}")
                        print(f"Stop Loss: {stop_loss:.5f}")
                        print(f"Take Profit: {take_profit:.5f}")
                        print(f"Volume: {position_size}")
                        
                        # Execute the trade
                        try:
                            if signal == "BUY":
                                order_type = mt5.ORDER_TYPE_BUY
                            else:
                                order_type = mt5.ORDER_TYPE_SELL
                            
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": position_size,
                                "type": order_type,
                                "price": entry_price,
                                "sl": stop_loss,
                                "tp": take_profit,
                                "magic": 123456,
                                "comment": f"Balanced_{signal}",
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            
                            result = mt5.order_send(request)
                            
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                trades_executed += 1
                                print(f"✅ TRADE EXECUTED! Ticket: {result.order}")
                                print(f"Total trades executed: {trades_executed}")
                            else:
                                error_msg = result.comment if result else "Unknown error"
                                print(f"❌ Trade failed: {error_msg}")
                                
                        except Exception as e:
                            print(f"❌ Execution error: {e}")
                    
                    else:
                        # Show what's needed
                        if rsi <= 45 and rsi >= 55:
                            print("⏳ RSI in neutral zone (45-55)")
                        elif ema9 == ema21:
                            print("⏳ EMAs equal - waiting for crossover")
                        else:
                            print("⏳ Waiting for conditions to align")
                    
                    print("-" * 50)
                
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n✅ Balanced trading stopped")
        print(f"Total trades executed: {trades_executed}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    balanced_trading_system()