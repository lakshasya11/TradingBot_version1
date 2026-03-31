import MetaTrader5 as mt5
import numpy as np
import time
from datetime import datetime

def calculate_indicators_fast(rates):
    """Fast indicator calculation for tick-based analysis"""
    if len(rates) < 50:
        return None
    
    close = rates['close']
    high = rates['high']
    low = rates['low']
    
    # Fast RSI calculation (last 14 periods)
    deltas = np.diff(close[-15:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
    
    # Fast EMA calculation
    ema9 = np.mean(close[-9:])  # Simplified
    ema21 = np.mean(close[-21:])  # Simplified
    
    # Fast ATR calculation (last 10 periods)
    tr_list = []
    for i in range(-10, -1):
        if i < -len(high) + 1:
            continue
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1]) if i > -len(close) + 1 else tr1
        tr3 = abs(low[i] - close[i-1]) if i > -len(close) + 1 else tr1
        tr_list.append(max(tr1, tr2, tr3))
    
    atr = np.mean(tr_list) if tr_list else (np.mean(high[-10:]) - np.mean(low[-10:]))
    
    return {
        'rsi': rsi,
        'ema9': ema9,
        'ema21': ema21,
        'atr': atr
    }

def tick_based_trading_system():
    """Tick-based trading system - analyzes every price tick"""
    
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    # Login
    login = 5044214016
    password = "Tq-w6rPx"
    server = "MetaQuotes-Demo"
    
    if not mt5.login(login, password, server):
        print(f"Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return
    
    print("TICK-BASED TRADING SYSTEM - REAL-TIME ANALYSIS")
    print("=" * 60)
    print("Symbol: EURUSD | Risk: $20 | TICK-BY-TICK ANALYSIS")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    symbol = "EURUSD"
    risk_amount = 20
    last_tick_time = 0
    tick_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                time.sleep(0.1)
                continue
            
            # Check if this is a new tick
            if tick.time <= last_tick_time:
                time.sleep(0.1)
                continue
            
            last_tick_time = tick.time
            tick_count += 1
            current_price = tick.bid
            
            # Get recent candle data for indicators (every 10 ticks to save CPU)
            if tick_count % 10 == 0:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)
                if rates is None:
                    continue
                
                indicators = calculate_indicators_fast(rates)
                if not indicators:
                    continue
            else:
                # Skip indicator calculation for intermediate ticks
                time.sleep(0.1)
                continue
            
            print(f"\n[TICK #{tick_count}] Price: {current_price:.5f}")
            print("=" * 50)
            
            # STEP 1: ULTRA-RELAXED Signal Generation (TICK-BASED)
            rsi = indicators['rsi']
            ema9 = indicators['ema9']
            ema21 = indicators['ema21']
            atr = indicators['atr']
            
            # Get current and previous candle for color determination
            current_candle = {
                'open': rates['open'][-1],
                'close': rates['close'][-1],
                'high': rates['high'][-1],
                'low': rates['low'][-1]
            }
            
            is_green_candle = current_candle['close'] > current_candle['open']
            is_red_candle = current_candle['close'] < current_candle['open']
            
            # ULTRA-RELAXED CONDITIONS for maximum trades
            buy_conditions = (
                rsi > 30 and  # RELAXED: was 45
                ema9 >= ema21 * 0.999  # RELAXED: almost equal
            )
            
            sell_conditions = (
                rsi < 70 and  # RELAXED: was 55
                ema9 <= ema21 * 1.001  # RELAXED: almost equal
            )
            
            signal = "NONE"
            if buy_conditions:
                signal = "BUY"
            elif sell_conditions:
                signal = "SELL"
            
            print(f"STEP 1: RSI={rsi:.1f} | Signal={signal} | Ready={'True' if signal != 'NONE' else 'False'}")
            
            if signal == "NONE":
                continue
            
            # STEP 2: ALWAYS PASS (ULTRA-RELAXED)
            step2_valid = True
            print(f"STEP 2: PASS (RELAXED)")
            
            # STEP 3: ALWAYS PASS (ULTRA-RELAXED)
            step3_valid = True
            print(f"STEP 3: PASS (RELAXED)")
            
            # STEP 4: Order Placement Check
            account_info = mt5.account_info()
            if not account_info:
                continue
                
            available_balance = min(account_info.balance, account_info.equity)
            available_risk = min(risk_amount, available_balance)
            
            if available_risk < 5:  # RELAXED: minimum $5
                print(f"STEP 4: FAIL - Insufficient balance: ${available_risk:.2f}")
                continue
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                continue
            
            # Calculate entry price and stops
            tick_size = symbol_info.trade_tick_size
            
            if signal == "BUY":
                entry_price = tick.ask + tick_size
                stop_loss = entry_price - (atr * 1.2)  # NEW: ATR * 1.2
                take_profit = entry_price + (abs(entry_price - stop_loss) * 1.2)  # NEW: 1.2 RR
            else:
                entry_price = tick.bid - tick_size
                stop_loss = entry_price + (atr * 1.2)  # NEW: ATR * 1.2
                take_profit = entry_price - (abs(stop_loss - entry_price) * 1.2)  # NEW: 1.2 RR
            
            # Calculate volume
            stop_distance = abs(entry_price - stop_loss)
            if stop_distance > 0:
                point_value = symbol_info.trade_contract_size * symbol_info.point
                risk_per_point = available_risk / (stop_distance / symbol_info.point)
                raw_volume = risk_per_point / point_value
                
                min_vol = symbol_info.volume_min
                volume_step = symbol_info.volume_step
                volume = max(min_vol, round(raw_volume / volume_step) * volume_step)
            else:
                volume = symbol_info.volume_min
            
            print(f"STEP 4: Entry={entry_price:.5f} | Volume={volume:.2f}")
            
            # FINAL DECISION: EXECUTE (ULTRA-RELAXED)
            print(f"FINAL: Step1=True | Step4=True | Execute=True")
            print("=" * 50)
            print(f">>> EXECUTING {signal} TRADE <<<")
            print(f"Entry: {entry_price:.2f} | Volume: {volume:.2f}")
            print("=" * 50)
            
            # Execute trade
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': volume,
                'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                'price': entry_price,
                'sl': stop_loss,
                'tp': take_profit,
                'comment': 'Tick-Based System',
                'type_filling': mt5.ORDER_FILLING_IOC,
                'magic': 234567
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"[SUCCESS] TRADE EXECUTED: Ticket #{result.order}")
                print(f"-> Waiting 10 seconds before next trade...")
                time.sleep(10)  # Wait 10 seconds after successful trade
            else:
                error_msg = result.comment if result else "Unknown error"
                print(f"[FAILED] TRADE ERROR: {error_msg}")
                time.sleep(2)  # Wait 2 seconds after failed trade
            
    except KeyboardInterrupt:
        elapsed_time = time.time() - start_time
        actual_tick_rate = tick_count / elapsed_time if elapsed_time > 0 else 0
        print(f"\n\nAnalysis stopped by user")
        print(f"PERFORMANCE SUMMARY:")
        print(f"   Runtime: {elapsed_time:.1f} seconds")
        print(f"   Ticks Processed: {tick_count}")
        print(f"   Tick Rate: {actual_tick_rate:.1f} ticks/sec")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    tick_based_trading_system()