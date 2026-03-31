import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
from enhanced_strategy import EnhancedTradingStrategy
import time

def verify_indicators():
    """Verify RSI and SuperTrend calculations"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("🔍 INDICATOR VERIFICATION TEST")
    print("=" * 50)
    
    # Create strategy instance
    strategy = EnhancedTradingStrategy("XAUUSD", "M1")
    
    # Test for 10 iterations to see live values
    for i in range(10):
        print(f"\n--- Test {i+1}/10 ---")
        
        # Get analysis
        analysis = strategy.analyze_timeframe("M1")
        
        if analysis:
            rsi = analysis.get('rsi', 0)
            ema9 = analysis.get('ema9', 0)
            ema21 = analysis.get('ema21', 0)
            st_direction = analysis.get('supertrend_direction', 0)
            atr = analysis.get('atr', 0)
            close = analysis.get('close', 0)
            
            print(f"Current Price: {close:.2f}")
            print(f"RSI (14): {rsi:.2f}")
            print(f"EMA9: {ema9:.2f}")
            print(f"EMA21: {ema21:.2f}")
            print(f"SuperTrend Direction: {st_direction} ({'BULLISH' if st_direction == 1 else 'BEARISH' if st_direction == -1 else 'NEUTRAL'})")
            print(f"ATR: {atr:.2f}")
            
            # Test current conditions from your main file
            print(f"\n--- CURRENT SYSTEM CONDITIONS ---")
            
            # BUY conditions from your system
            buy_rsi = rsi > 30
            buy_ema = ema9 > ema21
            buy_supertrend = st_direction == 1
            print(f"BUY: RSI>30={buy_rsi} | EMA9>EMA21={buy_ema} | ST=1={buy_supertrend}")
            buy_conditions_met = buy_rsi and buy_ema and buy_supertrend
            print(f"BUY Signal: {buy_conditions_met}")
            
            # SELL conditions from your system
            sell_rsi = rsi < 70
            sell_ema = ema9 < ema21
            sell_supertrend = st_direction == -1
            print(f"SELL: RSI<70={sell_rsi} | EMA9<EMA21={sell_ema} | ST=-1={sell_supertrend}")
            sell_conditions_met = sell_rsi and sell_ema and sell_supertrend
            print(f"SELL Signal: {sell_conditions_met}")
            
            # Final signal
            if buy_conditions_met:
                signal = "BUY"
            elif sell_conditions_met:
                signal = "SELL"
            else:
                signal = "NONE"
            
            print(f"FINAL SIGNAL: {signal}")
            
            # Check what enhanced_strategy thinks
            strategy_signal = strategy.check_entry_conditions(analysis)
            print(f"STRATEGY SIGNAL: {strategy_signal}")
            
            if signal != strategy_signal:
                print(f"⚠️  MISMATCH: Main={signal} vs Strategy={strategy_signal}")
            else:
                print(f"✅ MATCH: Both systems agree on {signal}")
                
        else:
            print("❌ No analysis data available")
        
        time.sleep(2)  # Wait 2 seconds between tests
    
    print(f"\n" + "=" * 50)
    print("🔍 VERIFICATION COMPLETE")
    
    mt5.shutdown()

if __name__ == "__main__":
    verify_indicators()