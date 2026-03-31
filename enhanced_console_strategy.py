import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_strategy import EnhancedTradingStrategy
import time
from dotenv import load_dotenv
import MetaTrader5 as mt5

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_dashboard(strategy):
    clear_screen()
    
    # Get current analysis
    analysis = strategy.analyze_timeframe(strategy.base_timeframe)
    
    print("=" * 60)
    print("         ENHANCED ATR TRADING STRATEGY DASHBOARD")
    print("=" * 60)
    print(f"Symbol: {strategy.symbol} | Timeframe: {strategy.base_timeframe}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if analysis:
        rsi = analysis.get('rsi', 0)
        ema9 = analysis.get('ema9', 0)
        ema21 = analysis.get('ema21', 0)
        st_dir = analysis.get('supertrend_direction', 0)
        atr = analysis.get('atr', 0)
        close = analysis.get('close', 0)
        
        # Entry conditions check
        signal = strategy.check_entry_conditions(analysis)
        
        print("MARKET DATA:")
        print(f"  Current Price: {close:.5f}")
        print(f"  ATR (10):      {atr:.5f}")
        print()
        
        print("TECHNICAL INDICATORS:")
        print(f"  RSI (14):      {rsi:.2f}  {'✅' if rsi > 50 else '❌' if rsi < 40 else '⚠️'}")
        print(f"  EMA 9:         {ema9:.5f}")
        print(f"  EMA 21:        {ema21:.5f}  {'✅' if ema9 > ema21 else '❌'}")
        print(f"  Supertrend:    {st_dir}     {'✅' if st_dir == 1 else '❌' if st_dir == -1 else '⚠️'}")
        print()
        
        print("ENTRY CONDITIONS:")
        print(f"  BUY Conditions:  RSI>50 ✅ | EMA9>EMA21 {'✅' if ema9 > ema21 else '❌'} | ST=1 {'✅' if st_dir == 1 else '❌'}")
        print(f"  SELL Conditions: RSI<40 {'✅' if rsi < 40 else '❌'} | EMA9<EMA21 {'✅' if ema9 < ema21 else '❌'} | ST=-1 {'✅' if st_dir == -1 else '❌'}")
        print()
        
        if signal != "NONE":
            print(f"🎯 SIGNAL: {signal}")
        else:
            print("⏳ WAITING FOR SIGNAL...")
        
        # Check positions
        positions = mt5.positions_get(symbol=strategy.symbol)
        if positions:
            print()
            print("OPEN POSITIONS:")
            for pos in positions:
                pnl_color = "🟢" if pos.profit > 0 else "🔴" if pos.profit < 0 else "⚪"
                print(f"  {pos.type_str} | Volume: {pos.volume} | P&L: {pos.profit:.2f} {pnl_color}")
        else:
            print()
            print("POSITIONS: None")
    
    print("=" * 60)
    print("Press Ctrl+C to stop")
    print("=" * 60)

def main():
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    # Create strategy
    strategy = EnhancedTradingStrategy("XAUUSD", "M15")
    
    try:
        while True:
            display_dashboard(strategy)
            
            # Run strategy logic
            analysis = strategy.analyze_timeframe(strategy.base_timeframe)
            if analysis:
                signal = strategy.check_entry_conditions(analysis)
                if signal != "NONE":
                    positions = mt5.positions_get(symbol=strategy.symbol)
                    if not positions:
                        strategy.execute_trade(signal, analysis)
                
                strategy.check_exit_conditions()
            
            time.sleep(0.5)  # Update every 0.5 seconds for real-time
            
    except KeyboardInterrupt:
        clear_screen()
        print("Strategy stopped by user")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()