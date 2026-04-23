# EMA 7 Strategy Configuration
# Entry angle thresholds for EMA 7 trend detection

# EMA 7 Angle Thresholds - COMMENTED OUT
# EMA7_ANGLE_BUY_THRESHOLD = 80.0   # Must be steeper than +80 degrees
# EMA7_ANGLE_SELL_THRESHOLD = -80.0 # Must be steeper than -80 degrees SELL signals

# Other EMA 7 strategy parameters - COMMENTED OUT
# EMA_PERIOD = 7
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30    # RSI must be > 30 for BUY
RSI_SELL_THRESHOLD = 70   # RSI must be < 70 for SELL
SIDEWAYS_THRESHOLD = 0.3  # EMA 7 range threshold for sideways detection
SIDEWAYS_LOOKBACK = 10    # Number of candles for sideways analysis

# Exit parameters
FIXED_SL_POINTS = 1.0     # Fixed stop loss distance in points
TP_POINTS = 4.0           # Take profit distance in points
TRAILING_POINTS = 0.01    # Points profit needed to activate trailing stop
TRAILING_GAP = 1.0        # Points trail behind current price
REVERSAL_EXIT_POINTS = 0.5 # Opposite candle reversal points

# print(f"EMA 7 Config loaded: BUY angle > {EMA7_ANGLE_BUY_THRESHOLD}°, SELL angle < {EMA7_ANGLE_SELL_THRESHOLD}°")