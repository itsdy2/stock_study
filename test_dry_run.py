# Test script for syntax and basic logic
import sys
import os

print("Checking syntax and imports...")

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sqlalchemy import Column, Integer, String
    import io
    import base64
    import json
    
    print("All libraries imported successfully.")
    
    # Simple logic test (non-DB part)
    def test_plot():
        plt.figure()
        plt.plot([1, 2, 3], [4, 5, 6])
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        print(f"Base64 Plot Generated, length: {len(b64)}")

    test_plot()
    print("Verification OK")

except Exception as e:
    print(f"Verification Failed: {e}")
    import traceback
    traceback.print_exc()
