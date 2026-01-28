# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os
import datetime
from sklearn.preprocessing import MinMaxScaler
from .setup import P

COL_OSC = '#6A5ACD'       
COL_PRICE = '#2F2F2F'     
GRID_ALPHA = 0.3

try:
    import yfinance as yf
except ImportError:
    yf = None

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

def get_live_data(ticker, period="1y"):
    """Fetch live data from yfinance"""
    if yf is None: return None
    try:
        df = yf.download(ticker, period=period, progress=False, threads=False)
        if df.empty: return None
        # Flatten columns if multi-index (yfinance update)
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, level=1, axis=1) if ticker in df.columns.levels[1] else df
            # Fallback if structure is different
            if 'Close' in df.columns and isinstance(df['Close'], pd.DataFrame):
                 df = df['Close'] # Just take close if confused, but we need OHLC? 
                 # Actually yfinance returns 'Open', 'High', 'Low', 'Close', 'Volume' columns.
                 # If flattened:
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Close': 'Close'}) # Ensure columns
        return df[['Date', 'Close']]
    except Exception as e:
        P.logger.error(f"Live data fetch failed for {ticker}: {e}")
        return None

def calculate_macd(df, col):
    df = df.copy()
    ema12 = df[col].ewm(span=12, adjust=False).mean()
    ema26 = df[col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df['Oscillator'] = macd - signal
    df['MACD'] = macd
    df['Signal'] = signal
    return df

def calculate_impulse(df, price_col):
    df = df.copy()
    df['EMA13'] = df[price_col].ewm(span=13, adjust=False).mean()
    
    # MACD for Impulse
    ema12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema26 = df[price_col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = macd - signal
    
    colors = []
    # Vectorized or loop? Loop is clearer for coloring logic
    ema = df['EMA13'].values
    hist = df['MACD_Hist'].values
    
    for i in range(len(df)):
        if i == 0:
            colors.append('gray')
            continue
        ema_up = ema[i] > ema[i-1]
        ema_down = ema[i] < ema[i-1]
        hist_up = hist[i] > hist[i-1]
        hist_down = hist[i] < hist[i-1]
        
        if ema_up and hist_up: colors.append('green')
        elif ema_down and hist_down: colors.append('red')
        else: colors.append('blue')
    
    df['Color'] = colors
    return df

def add_td_setup(df, price_col):
    prices = df[price_col].values
    sell = np.zeros(len(df))
    buy = np.zeros(len(df))
    
    for i in range(len(df)):
        if i >= 4 and prices[i] > prices[i-4]:
            sell[i] = sell[i-1] + 1
        else: sell[i] = 0
            
        if i >= 2 and prices[i] < prices[i-2]:
            buy[i] = buy[i-1] + 1
        else: buy[i] = 0
        
    df['TD_Sell'] = sell
    df['TD_Buy'] = buy
    return df

def plot_impulse(df, price_col, title):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['Date'], df[price_col], color='gray', alpha=0.5, linewidth=1)
    ax.scatter(df['Date'], df[price_col], c=df['Color'], s=10)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig_to_b64(fig)

def plot_td_setup(df, price_col, title):
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(df['Date'], df[price_col], color='black', linewidth=1)
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    
    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df['TD_Sell'], color='red', linewidth=1, label='Setup Sell (9)')
    ax2.plot(df['Date'], df['TD_Buy'], color='blue', linewidth=1, label='Setup Buy (9)')
    ax2.set_ylabel('Count')
    ax2.legend(loc='upper left')
    
    plt.title(title)
    plt.tight_layout()
    return fig_to_b64(fig)

def analyze(P):
    """
    Hybrid Analyzer: 
    1. YFinance for Live Price-based indicators (Impulse, DeMark)
    2. Excel for Historical Fear & Greed (if available)
    """
    results = []
    
    # 1. LIVE DATA Analysis (KOSPI/KOSDAQ)
    if yf:
        indices = [('^KS11', 'KOSPI'), ('^KQ11', 'KOSDAQ')]
        for ticker, name in indices:
            df = get_live_data(ticker, period="1y")
            if df is not None:
                # Impulse
                df_imp = calculate_impulse(df, 'Close')
                # DeMark
                df_td = add_td_setup(df, 'Close')
                
                # Plot Impulse
                img_imp = plot_impulse(df_imp, 'Close', f'{name} - Elder Impulse (Live)')
                results.append({
                    'key': f'imp_{name}', 'type': 'image', 'title': f'{name} Impulse (Live)',
                    'data': img_imp, 'order': 20
                })
                
                # Plot TD
                img_td = plot_td_setup(df_td, 'Close', f'{name} - DeMark TD (Live)')
                results.append({
                    'key': f'td_{name}', 'type': 'image', 'title': f'{name} DeMark TD (Live)',
                    'data': img_td, 'order': 21
                })
                
    # 2. EXCEL DATA Analysis (Fear & Greed)
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fear_greed_data.xlsx')
    if os.path.exists(data_path):
        try:
            # Need openpyxl
            import openpyxl
            k_df = pd.read_excel(data_path, sheet_name='KOSPI')
            q_df = pd.read_excel(data_path, sheet_name='KOSDAQ')
            
            # Simple Processing for F&G Oscillator visualization
            # Assuming file has pre-calc columns or we calc them?
            # The user's script calculated everything. We need to duplicate that if we want F&G.
            # For now, let's just assume we can read columns if they exist, or skip.
            # Simplified: Use existing script logic if possible, or just plot Price vs Oscillator if pre-calced.
            pass 
            # (Limitation: F&G calc logic is complex and needs many columns. 
            #  If user updates Excel, it works. Automation of this part is pending.)
        except Exception as e:
            P.logger.error(f"Excel read error: {e}")

    return results
