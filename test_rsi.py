"""
Test RSI calculation to verify it's working correctly
"""
import pandas as pd
import numpy as np
from indicators import TechnicalIndicators

def test_rsi_calculation():
    """Test RSI with known data"""
    
    # Create test data - trending up (should have RSI > 50)
    prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120]
    close_series = pd.Series(prices)
    
    print("=== RSI CALCULATION TEST ===")
    print(f"Test data (trending up): {prices[-5:]}")  # Show last 5 prices
    
    # Calculate RSI
    rsi = TechnicalIndicators.calculate_rsi(close_series, 14)
    
    print(f"RSI Series length: {len(rsi)}")
    print(f"RSI last 5 values: {rsi.tail(5).tolist()}")
    print(f"Final RSI: {rsi.iloc[-1]:.2f}")
    
    # Test with declining prices (should have RSI < 50)
    declining_prices = [120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100]
    declining_series = pd.Series(declining_prices)
    
    print("\n=== DECLINING PRICES TEST ===")
    print(f"Test data (trending down): {declining_prices[-5:]}")
    
    rsi_declining = TechnicalIndicators.calculate_rsi(declining_series, 14)
    print(f"Final RSI (declining): {rsi_declining.iloc[-1]:.2f}")
    
    # Test with real-like XAUUSD data
    xauusd_prices = [2650.50, 2651.20, 2649.80, 2652.10, 2653.40, 2651.90, 2654.20, 2655.10, 2653.70, 2656.30, 
                     2657.80, 2656.40, 2658.90, 2660.20, 2659.10, 2661.50, 2662.80, 2661.20, 2663.40, 2664.90, 2663.50]
    
    xauusd_series = pd.Series(xauusd_prices)
    print(f"\n=== XAUUSD-LIKE DATA TEST ===")
    print(f"XAUUSD prices: {xauusd_prices[-5:]}")
    
    rsi_xauusd = TechnicalIndicators.calculate_rsi(xauusd_series, 14)
    print(f"Final RSI (XAUUSD): {rsi_xauusd.iloc[-1]:.2f}")
    
    # Check for NaN values
    nan_count = rsi_xauusd.isna().sum()
    print(f"NaN values in RSI: {nan_count}")
    
    # Test entry conditions
    print(f"\n=== ENTRY CONDITION TESTS ===")
    print(f"RSI > 30 (BUY condition): {rsi_xauusd.iloc[-1] > 30}")
    print(f"RSI < 70 (SELL condition): {rsi_xauusd.iloc[-1] < 70}")
    
    return rsi_xauusd.iloc[-1]

if __name__ == "__main__":
    final_rsi = test_rsi_calculation()
    print(f"\n✅ RSI calculation test completed. Final RSI: {final_rsi:.2f}")