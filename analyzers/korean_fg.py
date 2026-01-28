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
    DB-Driven Analyzer: 
    Uses data from ModelKoreanMarket (collected via logic_collector.py).
    """
    results = []
    
    # 1. Fetch from DB
    try:
        from ..models import ModelKoreanMarket
        items = ModelKoreanMarket.get_data_by_days(days=365)
        
        if not items:
            return {
                'type': 'text',
                'title': 'Korean Market Data Error',
                'data': '데이터베이스에 한국 시장 데이터가 없습니다. (수집 실패 또는 초기화 중)'
            }
            
        # Convert to DataFrame
        data_list = []
        for item in items:
            data_list.append({
                'Date': item.date,
                'KOSPI': item.kospi,
                'KOSDAQ': item.kosdaq,
                'VIX': item.vix,
                'Bond3Y': item.bond_3y,
                'Bond10Y': item.bond_10y
            })
        
        df = pd.DataFrame(data_list)
        df = df.set_index('Date').sort_index()
        df = df.reset_index() # Impulse/DeMark functions expect 'Date' column
        
        # 2. Analyze KOSPI
        if 'KOSPI' in df.columns:
            # Dropna for KOSPI
            df_k = df[['Date', 'KOSPI']].dropna().rename(columns={'KOSPI': 'Close'})
            if not df_k.empty:
                df_imp = calculate_impulse(df_k, 'Close')
                df_td = add_td_setup(df_k, 'Close')
                
                results.append({
                    'key': 'imp_kospi', 'type': 'image', 'title': 'KOSPI Impulse (DB Data)',
                    'data': plot_impulse(df_imp, 'Close', 'KOSPI - Elder Impulse'), 'order': 20
                })
                results.append({
                    'key': 'td_kospi', 'type': 'image', 'title': 'KOSPI DeMark TD (DB Data)',
                    'data': plot_td_setup(df_td, 'Close', 'KOSPI - DeMark TD'), 'order': 21
                })

        # 3. Analyze KOSDAQ
        if 'KOSDAQ' in df.columns:
            df_q = df[['Date', 'KOSDAQ']].dropna().rename(columns={'KOSDAQ': 'Close'})
            if not df_q.empty:
                df_imp = calculate_impulse(df_q, 'Close')
                df_td = add_td_setup(df_q, 'Close')
                
                results.append({
                    'key': 'imp_kosdaq', 'type': 'image', 'title': 'KOSDAQ Impulse (DB Data)',
                    'data': plot_impulse(df_imp, 'Close', 'KOSDAQ - Elder Impulse'), 'order': 22
                })
                results.append({
                    'key': 'td_kosdaq', 'type': 'image', 'title': 'KOSDAQ DeMark TD (DB Data)',
                    'data': plot_td_setup(df_td, 'Close', 'KOSDAQ - DeMark TD'), 'order': 23
                })

        # 4. Fear & Greed (Placeholder logic for future implementation)
        # We have VIX and Bonds in DF now.
        # df['YieldGap'] = df['Bond10Y'] - df['Bond3Y']
        # can plot this?
        if 'Bond10Y' in df.columns and 'Bond3Y' in df.columns:
            df_bond = df[['Date', 'Bond10Y', 'Bond3Y']].dropna()
            if not df_bond.empty:
                df_bond['Spread'] = df_bond['Bond10Y'] - df_bond['Bond3Y']
                # Plot spread?
                pass

    except Exception as e:
        P.logger.error(f"Korean DB Analysis Error: {e}")
        import traceback
        P.logger.error(traceback.format_exc())
        return {
            'type': 'text',
            'title': 'Analysis Error',
            'data': str(e)
        }

    return results
