import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy
from trade_logger import TradeLogger

def live_trading():
    load_dotenv()
    
    # Initialize MT5
    if not mt5.initialize(path=os.getenv("MT5_PATH"), login=int(os.getenv("MT5_LOGIN")), 
                         password=os.getenv("MT5_PASSWORD"), server=os.getenv("MT5_SERVER")):
        print(f"MT5 failed: {mt5.last_error()}")
        return
    
    # Safety check
    account = mt5.account_info()
    if account and account.trade_mode != 0:
        print("LIVE ACCOUNT DETECTED!")
        if input("Type 'LIVE' to confirm: ") != 'LIVE':
            print("Cancelled")
            return
    
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    entry_manager = AdvancedEntryManager()
    logger = TradeLogger()
    
    print("LIVE TRADING SYSTEM ACTIVE")
    print("Press Ctrl+C to stop")
    
    tick_count = 0
    start_time = time.time()
    previous_price = None
    
    try:
        while True:
            symbol = "XAUUSD"
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                current_price = (tick.bid + tick.ask) / 2
                price_changed = (previous_price is None or abs(current_price - previous_price) > 0.0001)
                
                if price_changed:
                    tick_count += 1
                    previous_price = current_price
                    
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
                    if rates is not None and len(rates) >= 2:
                        analysis = strategy.analyze_timeframe("M1")
                        
                        if analysis:
                            rsi = analysis.get('rsi', 0)
                            ema9 = analysis.get('ema9', 0)
                            ema21 = analysis.get('ema21', 0)
                            atr = analysis.get('atr', 0)
                            
                            # Simple conditions
                            buy_signal = rsi > 45 and ema9 > ema21
                            sell_signal = rsi < 55 and ema9 < ema21
                            
                            if buy_signal or sell_signal:
                                signal = "BUY" if buy_signal else "SELL"
                                
                                print(f"\nTICK #{tick_count} | Price: {current_price:.2f}")
                                print(f"SIGNAL: {signal} | RSI: {rsi:.1f} | EMA9: {ema9:.2f} | EMA21: {ema21:.2f}")
                                
                                # Calculate entry price with tick adjustment
                                symbol_info = mt5.symbol_info(symbol)
                                if symbol_info:
                                    tick_size = symbol_info.trade_tick_size
                                    if signal == "BUY":
                                        entry_price = tick.ask + tick_size
                                        stop_loss = current_price - (atr * 1.1)
                                        take_profit = current_price + (atr * 1.1 * 2.0)
                                    else:
                                        entry_price = tick.bid - tick_size
                                        stop_loss = current_price + (atr * 1.1)
                                        take_profit = current_price - (atr * 1.1 * 2.0)
                                    
                                    # Calculate volume
                                    raw_volume, _ = entry_manager.order_logic.calculate_position_size(symbol, entry_price, stop_loss)
                                    min_vol = symbol_info.volume_min
                                    volume_step = symbol_info.volume_step
                                    volume = max(min_vol, round(raw_volume / volume_step) * volume_step)
                                    
                                    print(f"Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                                    print(f"Volume: {volume} | Risk: $100")
                                    
                                    # LIVE ORDER PLACEMENT
                                    result = mt5.order_send({
                                        'action': mt5.TRADE_ACTION_DEAL,
                                        'symbol': symbol,
                                        'volume': volume,
                                        'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                                        'price': entry_price,
                                        'sl': stop_loss,
                                        'tp': take_profit,
                                        'comment': 'LiveBot',
                                        'type_filling': mt5.ORDER_FILLING_IOC,
                                        'magic': 123456
                                    })
                                    
                                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                        print(f"TRADE EXECUTED: Ticket #{result.order} at {result.price:.5f}")
                                    else:
                                        error_msg = result.comment if result else "Unknown error"
                                        print(f"TRADE FAILED: {error_msg}")
                            
                            time.sleep(1)  # 1 second between checks
            else:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\nStopped. Runtime: {elapsed:.1f}s | Ticks: {tick_count}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    live_trading()