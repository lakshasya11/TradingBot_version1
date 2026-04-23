# EMA 7 Trading Strategy

An automated MetaTrader 5 trading bot using EMA 7 trend detection, RSI, and breakout/pullback entry logic for forex and gold trading.

## Features

- **EMA 7 Trend Detection**: 7-period Exponential Moving Average for dynamic trend identification
- **RSI Filter**: 14-period RSI (Wilder's smoothing) for momentum confirmation
- **Breakout/Pullback Entry**: Price action based on previous candle analysis for precise entries
- **Sideways Market Detection**: Blocks trades when EMA 7 range < 0.3 points over 10 candles
- **Fixed 1-Point Stop Loss**: Hard stop loss at exactly 1.0 points from entry price (highest priority)
- **Dynamic Trailing Stop**: Activates after 0.01 points profit, trails 1.0 points behind price
- **Dynamic Volume Cap**: Positions sized automatically based on account balance, capped at $5000 capital usage

---

## How the Bot Works

The bot runs in a continuous loop (every 1 second) and performs the following on each cycle:

1. Fetches the latest OHLCV candle data from MT5 (M5 timeframe by default)
2. Calculates RSI(14), ATR(20), and EMA 7 trend indicator
3. Evaluates entry conditions against the latest candle
4. If a signal is found and no position is open, executes a market order
5. Monitors open positions and applies trailing stop logic

---

## Entry Conditions

### BUY Signal (Dual-Mode)
- **Trend-Following BUY:** Triggered in a **Strong Uptrend (Angle > +80°)** on a **GREEN** candle (Price must be Above EMA 7 and RSI > 30).
    - **Body Coverage Rule:** If the previous candle was **RED**, the price must exceed its **Open** price to enter.
- **Counter-Trend BUY:** Triggered in a **Strong Downtrend (Angle < -80°)** on a **GREEN after GREEN** pattern (RSI < 70).
- **Momentum Check:** Price must always be **greater than** the previous candle's close.
- **Sideways Filter:** Blocks trades if EMA 7 range < 0.3 points.

### SELL Signal (Dual-Mode)
- **Trend-Following SELL:** Triggered in a **Strong Downtrend (Angle < -80°)** on a **RED** candle (Price must be Below EMA 7 and RSI < 70).
    - **Body Coverage Rule:** If the previous candle was **GREEN**, the price must be below its **Open** price to enter.
- **Counter-Trend SELL:** Triggered in a **Strong Uptrend (Angle > +80°)** on a **RED after RED** pattern (RSI > 30).
- **Momentum Check:** Price must always be **less than** the previous candle's close.
- **Sideways Filter:** Blocks trades if EMA 7 range < 0.3 points.

### Additional Entry Filters
- **Immediate Execution**: No tick confirmations required (single tick entry)
- **Dynamic Volume**: Position size calculated based on account balance, capped at $5000 capital usage
- **Volume Safety**: Trades skipped if calculated volume is too small

---

## Exit Conditions

### Two-Phase Exit Management System

#### **Phase 1: Fixed 1-Point Stop Loss** (Highest Priority)
- **Always Active**: Hard stop loss at exactly **1.0 points** from entry price
- **BUY**: Exit when `tick.bid <= entry_price - 1.0`
- **SELL**: Exit when `tick.ask >= entry_price + 1.0`
- **Immediate Execution**: Triggers instantly when price hits the 1-point level
- **Takes Precedence**: Over all other exit conditions

#### **Phase 1.5: Opposite Candle + 0.5pt Reversal Exit** (Second Priority)
- **Activation**: Only on the **next candle** after entry (when candle color changes)
- **BUY Position + RED Candle**: Exit if price drops **0.5 points** from the RED candle's **open price**
- **SELL Position + GREEN Candle**: Exit if price rises **0.5 points** from the GREEN candle's **open price**
- **Key Reference**: Uses the **new candle's open price**, not entry price
- **One-Time Check**: Only triggers once per candle color change
- **Purpose**: Quick exit on immediate trend reversal signals

#### **Phase 2: Dynamic Trailing Stop** (After Profit)
- **Activation Trigger**: After **0.01 points profit** (measured from bid/ask at entry)
- **Trailing Distance**: **1.0 points** behind current price
- **BUY Trailing**: `current_bid - 1.0` (only moves up)
- **SELL Trailing**: `current_ask + 1.0` (only moves down)
- **Profit Measurement**: 
  - BUY: `tick.bid - reference_price` (bid at entry)
  - SELL: `reference_price - tick.ask` (ask at entry)

#### **Take Profit**
- **Fixed Target**: **4.0 points** from entry price
- **BUY**: `entry_price + 4.0`
- **SELL**: `entry_price - 4.0`

### Exit Priority Order
1. **Fixed 1-Point Stop Loss** (highest priority - always checked first)
2. **Opposite Candle + 0.5pt Reversal Exit** (second priority - next candle only)
3. **Dynamic Trailing Stop** (after 0.01 points profit)
4. **Take Profit** (4.0 points target)
5. **Broker SL/TP** (backup safety mechanism)

### Entry Execution
- **Immediate Execution**: Single tick entry system with no confirmation delays
- **No Tick Confirmations**: Trades execute immediately when all conditions are met
- **Real-time Analysis**: Runs every 1 second for responsive signal detection

### Sideways Market Filter
- **Blocks all trades** when market is sideways
- **Detection Method**: EMA 7 range < 0.3 points over last 10 candles
- **Status Display**: Shows "SIDEWAYS" when active
- **Purpose**: Prevents false signals during low-volatility periods

> Only one position per symbol is allowed at a time.

---

## EMA 7 Trend Detection

- EMA Period = 7 (7-period exponential moving average)
- Calculation: `EMA7 = close.ewm(span=7, adjust=False).mean()`
- Trend signals: `ut_buy` = price > EMA 7 | `ut_sell` = price < EMA 7
- Smooths price action while remaining responsive to trend changes

---

## Exit Conditions

### Fixed 1-Point Stop Loss (Highest Priority)
- **Hard stop loss** at exactly **1.0 points** from entry price
- BUY: `entry - 1.0 pts` (e.g., 4702.00 entry → 4701.00 exit)
- SELL: `entry + 1.0 pts` (e.g., 4700.00 entry → 4701.00 exit)
- Triggers **immediately** when price hits the 1-point level
- Takes precedence over all other exit conditions

### Dynamic Trailing Stop
- Activates after **0.01 points profit** (measured in points, not dollars)
- Trails **1.0 points** behind current price
- BUY: `current bid - 1.0 pts` (only moves up)
- SELL: `current ask + 1.0 pts` (only moves down)

### Exit Priority Order
1. **Fixed 1-Point Stop Loss** (highest priority)
2. **Opposite Candle + 0.5pt Reversal Exit** (second priority)
3. **Dynamic Trailing Stop** (after 0.01 points profit)
4. **Take Profit** (4.0 points target)

---

## Live Log Format

Each tick outputs a single compact line with color coding:
```
[HH:MM:SS.mmm] Tick#N | Price: X | EMA7: X | EMA7_Angle: X° | RSI: X | Candle: GREEN/RED | EMA7_Buy: T/F | EMA7_Sell: T/F | Status: STATUS
```

**When in position, additional information is displayed:**
```
[HH:MM:SS.mmm] Tick#N | Price: X | EMA7: X | EMA7_Angle: X° | Candle: GREEN/RED | SL: X (Phase) | RSI: X | Status: IN POSITION | P/L: $X.XX
```

**Status Meanings:**
- **IN POSITION:** Currently holding a position
- **SIGNAL: BUY/SELL:** Entry conditions met, executing trade
- **SIDEWAYS:** Market conditions block trading (EMA 7 range < 0.3 points)
- **WAITING:** No signals detected, monitoring market

**Color Coding:**
- **Price:** Yellow/Orange
- **EMA7:** Red/Green
- **RSI:** Red/Green based on thresholds
- **Candle:** Green for bullish, Red for bearish
- **P/L:** Green for profit, Red for loss
- **Status:** Cyan for waiting, Green for in position, Magenta for signals

---

## Setup Instructions

### 1. Prerequisites
- MetaTrader 5 installed and running
- Python 3.8 or higher
- Active MT5 account

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file with your MT5 credentials:
```
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
```

### 4. Run the Bot
```bash
python flexible_entry_test.py
```

---

## Key Parameters (Actual Implementation)

### Entry Parameters
| Parameter | Value | Description |
|---|---|---|
| `ema_period` | 7 | EMA period for trend detection |
| `rsi_period` | 14 | RSI calculation period (Wilder's smoothing) |
| `rsi_buy_threshold` | 30 | RSI must be > 30 for BUY signals |
| `rsi_sell_threshold` | 70 | RSI must be < 70 for SELL signals |
| `ema7_angle_buy` | +77.0 | EMA 7 angle must be > +77° for BUY |
| `ema7_angle_sell` | -77.0 | EMA 7 angle must be < -77° for SELL |
| `sideways_threshold` | 0.3 | EMA 7 range threshold (points) for sideways detection |
| `sideways_lookback` | 10 | Number of candles for sideways analysis |

### Exit Parameters
| Parameter | Value | Description |
|---|---|---|
| `fixed_sl_points` | 1.0 | Fixed stop loss distance in points |
| `opposite_candle_exit_points` | 0.5 | Reversal exit threshold from candle open |
| `tp_points` | 4.0 | Take profit distance in points |
| `trailing_points` | 0.01 | Points profit needed to activate trailing stop |
| `trailing_gap` | 1.0 | Points trail behind current price |
| `atr_period` | 20 | ATR period for calculations |

### Volume & Risk Parameters
| Parameter | Value | Description |
|---|---|---|
| `capital_cap` | $5000 | Maximum capital usage per trade |
| `volume_calculation` | `balance/price` | Dynamic volume based on account balance |
| `min_volume` | 0.01 | Minimum trade volume |
| `session_capital` | $7149.74 | Starting session capital |

### System Parameters
| Parameter | Value | Description |
|---|---|---|
| `tick_interval` | 1 second | Strategy execution frequency |
| `chart_update_interval` | 5 ticks | Chart refresh frequency |
| `required_confirmations` | 0 | No tick confirmations (immediate entry) |
| `base_timeframe` | M5 | Primary analysis timeframe |

---

## File Structure

```
TradingBot_EMA_version-2/
├── enhanced_strategy.py           # Core strategy engine with breakout/pullback logic
├── flexible_entry_test.py         # Main trading bot runner
├── trade_backend/
│   ├── triple_strategy.py         # Multi-timeframe consensus strategy
│   ├── mt5_api_bridge.py          # MT5 API bridge
│   └── run_bot.py                 # Alternative bot runner
├── test_*.py                      # Testing and diagnostic files
├── requirements.txt
├── .env                           # MT5 credentials (not committed)
└── README.md
```

## Trading Symbols

Configured for:
- **XAUUSD** (Gold)
- **EURUSD** (Euro/Dollar)

## Disclaimer

This bot is for educational and research purposes. Trading forex and CFDs involves significant risk. Always test on a demo account before live trading.
