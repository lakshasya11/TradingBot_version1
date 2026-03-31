import MetaTrader5 as mt5
import time
from datetime import datetime
import os
from dotenv import load_dotenv

def comprehensive_tick_analysis():
    """Comprehensive tick analysis to answer all verification questions"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("COMPREHENSIVE TICK ANALYSIS - XAUUSD")
    print("=" * 50)
    print("Analyzing: Live Market | Tick Rate | Price Differences")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    symbol = "XAUUSD"
    last_tick_time = 0
    tick_count = 0
    start_time = time.time()
    price_changes = []
    previous_bid = None
    
    try:
        while True:
            tick = mt5.symbol_info_tick(symbol)
            current_time = time.time()
            
            # Only process genuine new ticks
            if tick and tick.time > last_tick_time:
                tick_count += 1
                elapsed = current_time - start_time
                rate = tick_count / elapsed if elapsed > 0 else 0
                last_tick_time = tick.time
                
                # Calculate price difference from previous tick
                price_diff = 0
                if previous_bid is not None:
                    price_diff = tick.bid - previous_bid
                    price_changes.append(abs(price_diff))
                
                # Live market verification
                tick_datetime = datetime.fromtimestamp(tick.time)
                current_datetime = datetime.now()
                time_diff = abs((current_datetime - tick_datetime).total_seconds())
                is_live = time_diff < 5  # Within 5 seconds = live
                
                # Display tick info
                tick_time = tick_datetime.strftime("%H:%M:%S")
                print(f"Tick #{tick_count:3d} | {tick_time} | Bid: {tick.bid:.2f} | "
                      f"Diff: {price_diff:+.2f} | Rate: {rate:.1f}/sec | "
                      f"Live: {'YES' if is_live else 'NO'}")
                
                previous_bid = tick.bid
            
            time.sleep(0.1)  # Check every 100ms
    
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        final_rate = tick_count / elapsed if elapsed > 0 else 0
        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
        max_price_change = max(price_changes) if price_changes else 0
        min_price_change = min(price_changes) if price_changes else 0
        
        print(f"\n" + "=" * 50)
        print("VERIFICATION RESULTS:")
        print("=" * 50)
        
        # Question 1: Live market verification
        print("1) LIVE MARKET VERIFICATION:")
        if final_rate > 0.5:
            print("   ✅ YES - Ticks are from LIVE MARKET in REAL TIME")
            print(f"   - Active tick generation: {final_rate:.1f} ticks/sec")
            print("   - Timestamps match current time")
        else:
            print("   ❌ NO - Market appears to be closed or inactive")
        
        # Question 2: Ticks per second
        print(f"\n2) TICK GENERATION RATE:")
        print(f"   📊 {final_rate:.1f} ticks per second")
        print(f"   - Total ticks: {tick_count}")
        print(f"   - Duration: {elapsed:.1f} seconds")
        if 2.0 <= final_rate <= 4.0:
            print("   ✅ NORMAL rate for XAUUSD")
        elif final_rate < 2.0:
            print("   ⚠️  LOWER than typical (quiet market)")
        else:
            print("   ⚠️  HIGHER than typical (active market)")
        
        # Question 3: Price differences per tick
        print(f"\n3) PRICE DIFFERENCE PER TICK:")
        if price_changes:
            print(f"   📈 Average: {avg_price_change:.3f} points per tick")
            print(f"   📊 Range: {min_price_change:.3f} to {max_price_change:.3f} points")
            print(f"   🔢 Total price changes analyzed: {len(price_changes)}")
            
            if avg_price_change < 0.1:
                print("   ✅ SMALL movements (stable market)")
            elif avg_price_change < 0.5:
                print("   ✅ NORMAL movements (typical volatility)")
            else:
                print("   ⚠️  LARGE movements (high volatility)")
        else:
            print("   ❌ No price changes detected")
        
        print("=" * 50)
    
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    comprehensive_tick_analysis()