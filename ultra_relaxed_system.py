import MetaTrader5 as mt5
import numpy as np
import time
from datetime import datetime

def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ema(prices, period):
    """Calculate EMA manually"""
    if len(prices) < period:
        return np.mean(prices)
    
    multiplier = 2 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    
    return ema

def calculate_atr(high, low, close, period=10):
    """Calculate ATR manually"""
    if len(high) < period + 1:
        return np.mean(high) - np.mean(low)
    
    tr_list = []
    for i in range(1, len(high)):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1])
        tr3 = abs(low[i] - close[i-1])
        tr_list.append(max(tr1, tr2, tr3))
    
    return np.mean(tr_list[-period:])

def ultra_relaxed_trading_system():
    """Ultra-relaxed trading system - WILL EXECUTE TRADES"""
    
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
    
    print("ULTRA-RELAXED TRADING SYSTEM - GUARANTEED TRADES")
    print("=" * 60)
    print("Symbol: EURUSD | Risk: $20 | RR: 1.2:1")
    print("RELAXED CONDITIONS FOR MAXIMUM TRADES")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    symbol = "EURUSD"
    risk_amount = 20
    
    try:
        while True:
            # Get market data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
            if rates is None:
                print("Failed to get market data")
                time.sleep(5)
                continue
            
            # Extract OHLC data
            high = rates['high']
            low = rates['low']
            close = rates['close']
            open_prices = rates['open']
            
            # Calculate indicators
            rsi = calculate_rsi(close, 14)
            ema9 = calculate_ema(close, 9)
            ema21 = calculate_ema(close, 21)
            atr = calculate_atr(high, low, close, 10)  # Period 10 for stops
            
            # Current and previous candles
            current_candle = {
                'open': open_prices[-1],
                'high': high[-1],
                'low': low[-1],
                'close': close[-1]
            }
            
            previous_candle = {
                'open': open_prices[-2],
                'high': high[-2],
                'low': low[-2],
                'close': close[-2]
            }
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ULTRA-RELAXED ANALYSIS")
            print("=" * 50)
            
            # STEP 1: ULTRA-RELAXED Signal Generation
            current_price = current_candle['close']
            is_green_candle = current_price > current_candle['open']
            is_red_candle = current_price < current_candle['open']
            
            # ULTRA-RELAXED BUY CONDITIONS: Just RSI > 30 and any trend
            buy_conditions = (
                rsi > 30 and  # RELAXED: was 45
                ema9 >= ema21 * 0.999  # RELAXED: almost equal is fine
            )
            
            # ULTRA-RELAXED SELL CONDITIONS: Just RSI < 70 and any trend
            sell_conditions = (
                rsi < 70 and  # RELAXED: was 55
                ema9 <= ema21 * 1.001  # RELAXED: almost equal is fine
            )
            
            signal = "NONE"
            if buy_conditions:
                signal = "BUY"
            elif sell_conditions:
                signal = "SELL"
            
            print(f"STEP 1 -> SIGNAL: {signal}")
            print(f"  RSI: {rsi:.1f} | EMA9: {ema9:.5f} | EMA21: {ema21:.5f}")
            print(f"  Candle: {'GREEN' if is_green_candle else 'RED' if is_red_candle else 'DOJI'}")
            print(f"  Conditions: {'PASS' if buy_conditions or sell_conditions else 'FAIL'}")
            
            if signal == "NONE":
                print("  -> Waiting for signal conditions...")
                time.sleep(3)
                continue
            
            # STEP 2: ULTRA-RELAXED Entry Logic
            body_size = abs(current_price - current_candle['open'])
            body_percentage = (body_size / current_price) * 100
            min_body_valid = body_percentage >= 0.001  # ULTRA-RELAXED: 0.001%
            
            # ULTRA-RELAXED Breakout logic - always pass
            breakout_valid = True  # ALWAYS PASS
            breakout_msg = "Breakout check bypassed (RELAXED)"
            
            step2_valid = True  # ALWAYS PASS
            
            print(f"\nSTEP 2 -> ENTRY LOGIC: PASS (RELAXED)")
            print(f"  Body: {body_percentage:.3f}% (RELAXED)")
            print(f"  {breakout_msg}")
            
            # STEP 3: ULTRA-RELAXED Enter Trading
            step3_valid = True  # ALWAYS PASS
            
            print(f"\nSTEP 3 -> ENTER TRADING: PASS (RELAXED)")
            print(f"  All conditions relaxed for maximum trades")
            
            # STEP 4: Order Placement
            # Check account balance
            account_info = mt5.account_info()
            available_balance = min(account_info.balance, account_info.equity) if account_info else 0
            available_risk = min(risk_amount, available_balance)
            
            if available_risk < 5:  # RELAXED: was 20
                print(f"\nSTEP 4 -> ORDER PLACEMENT: FAIL")
                print(f"  Error: Insufficient balance: ${available_risk:.2f} < $5")
                time.sleep(5)
                continue
            
            # Get market data
            tick = mt5.symbol_info_tick(symbol)
            symbol_info = mt5.symbol_info(symbol)
            
            if not tick or not symbol_info:
                print(f"\nSTEP 4 -> ORDER PLACEMENT: FAIL")
                print(f"  Error: Market data unavailable")
                time.sleep(5)
                continue
            
            # Enhanced pricing
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
            
            print(f"\nSTEP 4 -> ORDER PLACEMENT: PASS")
            print(f"  Entry: {entry_price:.5f} | SL: {stop_loss:.5f} | TP: {take_profit:.5f}")
            print(f"  Volume: {volume:.2f} | Risk: ${available_risk:.2f} | RR: 1.2:1")
            print(f"  Bid: {tick.bid:.5f} | Ask: {tick.ask:.5f}")
            
            # FINAL DECISION - ALWAYS EXECUTE IF WE GET HERE
            print(f"\nFINAL DECISION: EXECUTE")
            print(f"  [OK] EXECUTING {signal} TRADE - ULTRA-RELAXED MODE!")
            
            # Execute trade
            request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': volume,
                'type': mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                'price': entry_price,
                'sl': stop_loss,
                'tp': take_profit,
                'comment': 'Ultra-Relaxed System',
                'type_filling': mt5.ORDER_FILLING_IOC,
                'magic': 234567
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  [SUCCESS] TRADE EXECUTED: Ticket #{result.order} at {result.price:.5f}")
                print(f"  -> Waiting 30 seconds before next trade...")
                time.sleep(30)  # Wait 30 seconds after successful trade
            else:
                error_msg = result.comment if result else "Unknown error"
                print(f"  [FAILED] TRADE ERROR: {error_msg}")
                time.sleep(5)  # Wait 5 seconds after failed trade
            
    except KeyboardInterrupt:
        print("\n\nTrading system stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    ultra_relaxed_trading_system()