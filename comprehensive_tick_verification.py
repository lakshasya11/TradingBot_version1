import MetaTrader5 as mt5
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

def comprehensive_tick_verification():
    """Comprehensive verification of live tick data"""
    
    load_dotenv()
    
    # Initialize MT5
    mt5_path = os.getenv("MT5_PATH")
    mt5_login = int(os.getenv("MT5_LOGIN"))
    mt5_pass = os.getenv("MT5_PASSWORD")
    mt5_server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize(path=mt5_path, login=mt5_login, password=mt5_pass, server=mt5_server):
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return
    
    print("COMPREHENSIVE TICK VERIFICATION - XAUUSD")
    print("=" * 50)
    print("Analyzing live market data for 30 seconds...")
    print("Press Ctrl+C to stop early")
    print("=" * 50)
    
    symbol = "XAUUSD"
    last_tick_time = 0
    tick_count = 0
    start_time = time.time()
    price_changes = []
    previous_bid = None
    tick_timestamps = []
    
    try:
        while time.time() - start_time < 30:  # Run for 30 seconds
            tick = mt5.symbol_info_tick(symbol)
            current_time = time.time()
            
            # Only process genuine new ticks
            if tick and tick.time > last_tick_time:
                tick_count += 1
                elapsed = current_time - start_time
                rate = tick_count / elapsed if elapsed > 0 else 0
                last_tick_time = tick.time
                
                # Store tick timestamp for live verification
                tick_timestamps.append(tick.time)
                
                # Calculate price difference from previous tick
                price_diff = 0
                if previous_bid is not None:
                    price_diff = tick.bid - previous_bid
                    if abs(price_diff) > 0.001:  # Only count meaningful price changes
                        price_changes.append(abs(price_diff))
                
                # Convert to MT5 local time (matching your display)
                server_time = datetime.fromtimestamp(tick.time)
                local_mt5_time = server_time - timedelta(hours=5, minutes=30)
                
                # Live market verification
                current_datetime = datetime.now()
                server_datetime = datetime.fromtimestamp(tick.time)
                time_diff = abs((current_datetime - server_datetime).total_seconds())
                is_live = time_diff < 10  # Within 10 seconds = live
                
                # Display every 5th tick
                if tick_count % 5 == 0:
                    print(f"Tick #{tick_count:3d} | MT5: {local_mt5_time.strftime('%H:%M:%S')} | "
                          f"Price: {tick.bid:.2f} | Diff: {price_diff:+.3f} | "
                          f"Rate: {rate:.1f}/sec | Live: {'YES' if is_live else 'NO'}")
                
                previous_bid = tick.bid
            
            time.sleep(0.05)  # Check every 50ms
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    finally:
        elapsed = time.time() - start_time
        final_rate = tick_count / elapsed if elapsed > 0 else 0
        
        # Calculate statistics
        avg_price_change = sum(price_changes) / len(price_changes) if price_changes else 0
        max_price_change = max(price_changes) if price_changes else 0
        min_price_change = min(price_changes) if price_changes else 0
        
        # Live market verification
        if tick_timestamps:
            latest_tick = max(tick_timestamps)
            current_timestamp = time.time()
            time_delay = current_timestamp - latest_tick
            is_live_market = time_delay < 30  # Within 30 seconds
        else:
            is_live_market = False
            time_delay = 0
        
        print(f"\n" + "=" * 50)
        print("VERIFICATION RESULTS:")
        print("=" * 50)
        
        # Question 1: Live market verification
        print("1) LIVE MARKET VERIFICATION:")
        if is_live_market and final_rate > 0.5:
            print("   ✅ YES - Ticks are from LIVE MARKET in REAL TIME")
            print(f"   - Latest tick delay: {time_delay:.1f} seconds")
            print(f"   - Active tick generation: {final_rate:.1f} ticks/sec")
            print("   - Timestamps are current and updating")
        else:
            print("   ❌ NO - Market appears inactive or closed")
            print(f"   - Tick delay: {time_delay:.1f} seconds")
            print(f"   - Low activity: {final_rate:.1f} ticks/sec")
        
        # Question 2: Ticks per second
        print(f"\n2) TICK GENERATION RATE:")
        print(f"   📊 {final_rate:.1f} ticks per second")
        print(f"   - Total genuine ticks: {tick_count}")
        print(f"   - Analysis duration: {elapsed:.1f} seconds")
        if 2.0 <= final_rate <= 4.0:
            print("   ✅ NORMAL rate for XAUUSD during active hours")
        elif final_rate < 2.0:
            print("   ⚠️  LOWER than typical (quiet session or off-hours)")
        else:
            print("   ⚠️  HIGHER than typical (very active market)")
        
        # Question 3: Price differences per tick
        print(f"\n3) PRICE DIFFERENCE PER TICK:")
        if price_changes:
            print(f"   📈 Average price change: {avg_price_change:.4f} points per tick")
            print(f"   📊 Price change range: {min_price_change:.4f} to {max_price_change:.4f} points")
            print(f"   🔢 Meaningful price changes: {len(price_changes)} out of {tick_count} ticks")
            print(f"   📉 Price change percentage: {len(price_changes)/tick_count*100:.1f}% of ticks")
            
            if avg_price_change < 0.01:
                print("   ✅ VERY SMALL movements (consolidating market)")
            elif avg_price_change < 0.05:
                print("   ✅ SMALL movements (stable market)")
            elif avg_price_change < 0.1:
                print("   ✅ NORMAL movements (typical volatility)")
            else:
                print("   ⚠️  LARGE movements (high volatility period)")
        else:
            print("   ❌ No significant price changes detected")
            print("   - All ticks showed identical or minimal price differences")
        
        print("=" * 50)
        
        mt5.shutdown()

if __name__ == "__main__":
    comprehensive_tick_verification()