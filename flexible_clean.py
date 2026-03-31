import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import time
import os
from dotenv import load_dotenv
from advanced_entry_logic import CandleStructureValidator, MomentumValidator, BreakoutLogic, AdvancedEntryManager
from enhanced_strategy import EnhancedTradingStrategy

def complete_entry_analysis():
    """Flexible Entry Analysis - Much easier conditions"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    # Initialize components
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    validator = CandleStructureValidator()
    momentum_validator = MomentumValidator()
    breakout_logic = BreakoutLogic()
    entry_manager = AdvancedEntryManager()
    
    # Price history for momentum analysis
    price_history = []
    
    print("🚀 FLEXIBLE ENTRY ANALYSIS - LIVE TEST")
    print("=" * 70)
    print("FLEXIBLE CONDITIONS: BUY (RSI>45 + EMA9>EMA21) | SELL (RSI<55 + EMA9<EMA21)")
    print("Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        while True:
            # Get live market data
            symbol = "XAUUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 3)
            tick = mt5.symbol_info_tick(symbol)
            
            if rates is not None and len(rates) >= 2 and tick:
                df = pd.DataFrame(rates)
                
                # Get analysis
                analysis = strategy.analyze_timeframe("M1")
                
                # STEP 2: Candle Structure Validation
                current_candle = {
                    'open': df.iloc[-1]['open'],
                    'close': df.iloc[-1]['close'],
                    'high': df.iloc[-1]['high'],
                    'low': df.iloc[-1]['low']
                }
                
                previous_candle = {
                    'open': df.iloc[-2]['open'],
                    'close': df.iloc[-2]['close'],
                    'high': df.iloc[-2]['high'],
                    'low': df.iloc[-2]['low']
                }
                
                current_price = tick.bid
                
                # Update price history for momentum analysis
                price_history.append(current_price)
                if len(price_history) > 10:  # Keep last 10 prices
                    price_history = price_history[-10:]
                
                # UTC time
                utc_time = datetime.fromtimestamp(rates[-1]['time'], tz=timezone.utc)
                time_display = utc_time.strftime("%H:%M:%S")
                
                print(f"\n[{time_display} UTC] 🎯 FLEXIBLE ENTRY ANALYSIS")
                print("=" * 70)
                
                # Get all analysis data first
                if analysis:
                    rsi = analysis.get('rsi', 0)
                    ema9 = analysis.get('ema9', 0)
                    ema21 = analysis.get('ema21', 0)
                    st_dir = analysis.get('supertrend_direction', 0)
                    atr = analysis.get('atr', 0)
                    
                    # FLEXIBLE CONDITIONS - Much easier to satisfy
                    buy_rsi = rsi > 45
                    buy_ema = ema9 > ema21  
                    buy_conditions_met = buy_rsi and buy_ema

                    sell_rsi = rsi < 55
                    sell_ema = ema9 < ema21
                    sell_conditions_met = sell_rsi and sell_ema

                    print("🔍 STEP 1 → ENTRY CONDITIONS:")
                    print(f"  BUY:  RSI>45={buy_rsi} | EMA9>EMA21={buy_ema} → {'✅ READY' if buy_conditions_met else '❌ WAIT'}")
                    print(f"  SELL: RSI<55={sell_rsi} | EMA9<EMA21={sell_ema} → {'✅ READY' if sell_conditions_met else '❌ WAIT'}")

                    if buy_conditions_met:
                        signal = "BUY"
                        entry_conditions_met = True
                    elif sell_conditions_met:
                        signal = "SELL"
                        entry_conditions_met = True
                    else:
                        signal = "NONE"
                        entry_conditions_met = False
                    
                    # Step 4: Order Placement Analysis
                    print("\n💰 STEP 4 → ORDER PLACEMENT:")
                    
                    # Get market data for Step 4
                    market_data = entry_manager.order_logic.get_market_depth(symbol)
                    if 'error' not in market_data:
                        # Calculate stop loss using ATR
                        atr_value = analysis.get('atr', 0)
                        if signal == "BUY":
                            stop_loss = current_price - (atr_value * 1.1)
                            take_profit = current_price + (atr_value * 1.1 * 2.0)
                        else:
                            stop_loss = current_price + (atr_value * 1.1)
                            take_profit = current_price - (atr_value * 1.1 * 2.0)
                        
                        print(f"  Bid: {market_data.get('bid', 0):.5f} | Ask: {market_data.get('ask', 0):.5f}")
                        print(f"  SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
                        
                        order_ready = True
                        print(f"  Order Ready: ✅")
                    else:
                        print(f"  ❌ Market data error: {market_data.get('error', 'Unknown')}")
                        order_ready = False
                    
                    # FLEXIBLE FINAL DECISION - Only need Step 1 + Step 4
                    all_systems_go = entry_conditions_met and order_ready
                    
                    print("\n🚀 FINAL DECISION:")
                    if all_systems_go:
                        print(f"  🎆 EXECUTE {signal} TRADE NOW!")
                        print(f"  ✅ Ready for live order execution")
                        
                        # DIRECT ORDER EXECUTION
                        try:
                            if signal == "BUY":
                                order_type = mt5.ORDER_TYPE_BUY
                                entry_price = tick.ask
                            else:
                                order_type = mt5.ORDER_TYPE_SELL
                                entry_price = tick.bid
                            
                            # Simple order request
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": symbol,
                                "volume": 0.01,
                                "type": order_type,
                                "price": entry_price,
                                "sl": stop_loss,
                                "tp": take_profit,
                                "magic": 123456,
                                "comment": f"Flexible_{signal}",
                                "type_filling": mt5.ORDER_FILLING_IOC,
                            }
                            
                            result = mt5.order_send(request)
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                print(f"  ✅ TRADE EXECUTED! Ticket: {result.order}")
                            else:
                                error_msg = result.comment if result else "Unknown error"
                                print(f"  ❌ Trade failed: {error_msg}")
                                
                        except Exception as e:
                            print(f"  ❌ Execution error: {e}")
                        
                    else:
                        print(f"  ⏳ WAIT - Need EMA crossover and RSI in range (45-55)")
                else:
                    print("❌ No market data available")
                
                print("=" * 70)
                
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n\n✅ Flexible entry analysis stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    complete_entry_analysis()