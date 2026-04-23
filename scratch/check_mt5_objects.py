import MetaTrader5 as mt5
import sys

def check_mt5_objects():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    attrs = dir(mt5)
    obj_attrs = [a for a in attrs if "object" in a.lower()]
    print(f"Object-related attributes: {obj_attrs}")
    
    mt5.shutdown()

if __name__ == "__main__":
    check_mt5_objects()
