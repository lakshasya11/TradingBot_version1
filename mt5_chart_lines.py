import MetaTrader5 as mt5

class MT5ChartLines:
    """
    Utility class for chart visualization directly on MT5 terminal.
    Uses OBJ_HLINE objects to show internal exit levels.
    """
    
    @staticmethod
    def draw_horizontal_line(symbol, price, name, color, text, style=2, width=2):
        """Draw a horizontal line on the MT5 chart (style 2 = STYLE_DOT)"""
        try:
            # Create or update the line
            # MT5 Python API: object_create(name, type, chart, window, time, price)
            if not mt5.object_create(name, 1, 0, 0, 0, price):
                # If creation failed, try to move existing object
                if not mt5.object_move(name, 0, 0, price):
                    return False
            
            # Set properties - use try-except for each to be safe
            try: mt5.object_set_integer(name, 0, color)      # OBJPROP_COLOR = 0
            except: pass
            try: mt5.object_set_integer(name, 1, style)      # OBJPROP_STYLE = 1
            except: pass
            try: mt5.object_set_integer(name, 2, width)      # OBJPROP_WIDTH = 2
            except: pass
            try: mt5.object_set_string(name, 20, text)       # OBJPROP_TEXT = 20
            except: pass
            try: mt5.object_set_integer(name, 3, 0)          # OBJPROP_BACK = 3 (0=False)
            except: pass
            try: mt5.object_set_integer(name, 4, 0)          # OBJPROP_SELECTABLE = 4 (0=False)
            except: pass
            try: mt5.object_set_integer(name, 5, 0)          # OBJPROP_HIDDEN = 5 (0=False)
            except: pass
            
            return True
        except Exception:
            return False

    @staticmethod
    def safe_delete(name):
        """Safely delete an object with attribute checking"""
        try:
            if hasattr(mt5, 'object_delete'):
                mt5.object_delete(name)
            elif hasattr(mt5, 'ObjectDelete'):
                mt5.ObjectDelete(name)
            elif hasattr(mt5, 'objects_delete'):
                mt5.objects_delete(name)
        except:
            pass

    @staticmethod
    def update_position_lines(symbol, positions, position_data):
        """Draw visual lines on MT5 for all active positions"""
        try:
            if not positions:
                # Clear lines if no positions
                MT5ChartLines.safe_delete(f"{symbol}_FIXED_SL")
                MT5ChartLines.safe_delete(f"{symbol}_TRAILING_SL")
                MT5ChartLines.safe_delete(f"{symbol}_TP")
                return True

            for pos in positions:
                ticket = pos.ticket
                pos_data = position_data.get(ticket, {})
                direction = "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL"
                
                # 1. FIXED STOP LOSS (Red Dotted)
                fixed_sl = pos.price_open - 1.0 if direction == "BUY" else pos.price_open + 1.0
                MT5ChartLines.draw_horizontal_line(
                    symbol, fixed_sl, f"{symbol}_FIXED_SL", 
                    0x0000FF, # Red in BGR
                    f"Fixed SL #{ticket}", 
                    2, 2
                )
                
                # 2. TAKE PROFIT (Green Dotted)
                tp = pos.price_open + 4.0 if direction == "BUY" else pos.price_open - 4.0
                MT5ChartLines.draw_horizontal_line(
                    symbol, tp, f"{symbol}_TP", 
                    0x00FF00, # Green in BGR
                    f"Take Profit #{ticket}", 
                    2, 2
                )
                
                # 3. TRAILING STOP LOSS (Orange Dotted)
                if pos_data.get('dollar_trail_active', False):
                    trailing_sl = pos_data.get('dollar_trail_sl')
                    if trailing_sl:
                        MT5ChartLines.draw_horizontal_line(
                            symbol, trailing_sl, f"{symbol}_TRAILING_SL", 
                            0x0080FF, # Orange/Gold in BGR
                            f"Trailing SL #{ticket}", 
                            2, 2
                        )
                else:
                    # Remove trailing line if not active yet
                    MT5ChartLines.safe_delete(f"{symbol}_TRAILING_SL")
                    
            return True
        except Exception:
            return False