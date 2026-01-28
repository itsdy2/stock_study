# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from sklearn.preprocessing import MinMaxScaler
from .setup import P

# =============================
# Constants & Colors
# =============================
COL_OSC = '#6A5ACD'       # Fear & Greed
COL_PRICE = '#2F2F2F'     # Price
COL_SUPERMA = '#FF8C00'   # SuperMA
COL_GAP = '#00B3B3'       # Gap%
GRID_ALPHA = 0.3

def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img

# =============================
# Indicator Logic (Ported)
# =============================

def calculate_rsi(df, col, window=10):
    df = df.copy()
    delta = df[col].diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window).mean()
    rs = gain / loss
    df['RSI_10'] = 100 - (100 / (1 + rs))
    return df

def calculate_fear_greed(df, index_col, vix_col, call_col, put_col, bond5_col, bond10_col):
    df = df.copy()

    df['MA125'] = df[index_col].rolling(125).mean()
    df['Momentum'] = (df[index_col] - df['MA125']) / df['MA125'] * 100
    
    # Safety: replace 0 with nan to avoid division by zero
    df['PutCall'] = df[put_col] / df[call_col].replace(0, np.nan)
    
    df['Volatility'] = df[vix_col]
    df['BondDiff'] = df[bond10_col] - df[bond5_col]

    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    features = ['Momentum','PutCall','Volatility','BondDiff','RSI_10']
    
    # Must have all features to calc
    valid = df.dropna(subset=features).index

    df['Fear_Greed_Index'] = np.nan
    if len(valid) == 0:
        return df

    scaler = MinMaxScaler()
    # Fit only on valid rows
    df.loc[valid, features] = scaler.fit_transform(df.loc[valid, features])

    df.loc[valid, 'Fear_Greed_Index'] = (
        df.loc[valid,'Momentum'] * 0.2 +
        (1 - df.loc[valid,'PutCall']) * 0.2 +
        (1 - df.loc[valid,'Volatility']) * 0.2 +
        df.loc[valid,'BondDiff'] * 0.2 +
        df.loc[valid,'RSI_10'] * 0.2
    )
    return df

def calculate_macd(df, col):
    df = df.copy()
    ema12 = df[col].ewm(span=12, adjust=False).mean()
    ema26 = df[col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df['Oscillator'] = macd - signal
    return df

def add_super_ma_gap(df, price_col, label):
    df = df.copy()
    for w in [20,60,120,200]:
        df[f'{label}_MA{w}'] = df[price_col].rolling(w).mean()
    mas = [f'{label}_MA{w}' for w in [20,60,120,200]]
    df[f'{label}_SuperMA'] = df[mas].mean(axis=1)
    df[f'{label}_GapPct'] = (df[price_col] - df[f'{label}_SuperMA']) / df[f'{label}_SuperMA'] * 100
    return df

def add_impulse_components(df, price_col, label):
    df = df.copy()
    df[f'{label}_EMA13'] = df[price_col].ewm(span=13, adjust=False).mean()
    ema12 = df[price_col].ewm(span=12, adjust=False).mean()
    ema26 = df[price_col].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    df[f'{label}_MACD_Hist'] = macd - signal
    return df

def get_impulse_colors(df, ema_col, macd_col):
    colors = []
    # Vectorized logic might be faster but loop is safe
    ema = df[ema_col].values
    hist = df[macd_col].values
    
    for i in range(len(df)):
        if i == 0:
            colors.append('gray')
            continue
        ema_up = ema[i] > ema[i-1]
        ema_down = ema[i] < ema[i-1]
        hist_up = hist[i] > hist[i-1]
        hist_down = hist[i] < hist[i-1]

        if ema_up and hist_up:
            colors.append('green')
        elif ema_down and hist_down:
            colors.append('red')
        else:
            colors.append('blue')
    return colors

def add_td_setup_counts(df, price_col, label='TD'):
    df = df.copy()
    prices = df[price_col].values
    sell = np.zeros(len(df))
    buy = np.zeros(len(df))

    for i in range(len(df)):
        if i >= 4 and prices[i] > prices[i-4]:
            sell[i] = sell[i-1] + 1
        else:
            sell[i] = 0

        if i >= 2 and prices[i] < prices[i-2]:
            buy[i] = buy[i-1] + 1
        else:
            buy[i] = 0

    df[f'{label}_SellSetup'] = sell
    df[f'{label}_BuySetup'] = buy
    return df

# =============================
# Plotting Functions
# =============================

def plot_fg(df, price_col, title):
    fig, ax1 = plt.subplots(figsize=(10, 5)) # Adjusted size for web
    ax1.plot(df['Date'], df['Oscillator'], color=COL_OSC, linewidth=2, label='Fear & Greed Oscillator')
    ax1.set_ylabel('Fear & Greed', color=COL_OSC)
    ax1.tick_params(axis='y', labelcolor=COL_OSC)
    ax1.grid(True, alpha=GRID_ALPHA)

    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df[price_col], color=COL_PRICE, linewidth=1, label=price_col)
    ax2.set_ylabel(price_col, color=COL_PRICE)
    ax2.tick_params(axis='y', labelcolor=COL_PRICE)

    # Legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.title(title)
    plt.tight_layout()
    return fig_to_b64(fig)

def plot_impulse_chart(df, price_col, ema_col, macd_col, title):
    colors = get_impulse_colors(df, ema_col, macd_col)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['Date'], df[price_col], color=COL_PRICE, linewidth=1)
    ax.scatter(df['Date'], df[price_col], c=colors, s=10) # Smaller dots
    ax.grid(True, alpha=GRID_ALPHA)
    ax.set_title(title)
    plt.tight_layout()
    return fig_to_b64(fig)

def plot_demark_daily(df, price_col, title):
    label = 'TD'
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(df['Date'], df[price_col], color=COL_PRICE, linewidth=1, label=price_col)
    ax1.set_ylabel(price_col, color=COL_PRICE)
    ax1.grid(True, alpha=GRID_ALPHA)

    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df[f'{label}_SellSetup'], color='red', linewidth=1, label='TD Sell Setup')
    ax2.plot(df['Date'], df[f'{label}_BuySetup'], color='blue', linewidth=1, label='TD Buy Setup')
    ax2.set_ylabel('TD Setup Count')

    # lines = ax1.get_lines() + ax2.get_lines()
    # ax1.legend(lines, [l.get_label() for l in lines], loc='upper left')
    plt.title(title)
    plt.tight_layout()
    return fig_to_b64(fig)


# =============================
# Main Analyze Function
# =============================
def analyze(P):
    results = []
    
    # 1. Fetch Data
    try:
        from ..models import ModelKoreanMarket
        items = ModelKoreanMarket.get_data_by_days(days=400) # Need > 365 for MA200 + 125 calc
        
        if not items:
            return [{'type': 'text', 'title': 'Data Error', 'data': 'No Data in DB'}]

        data_list = []
        for item in items:
            data_list.append({
                'Date': item.date,
                '코스피': item.kospi,
                '코스닥': item.kosdaq,
                '코스피 200 변동성지수': item.vix,
                '5년 국채선물 추종 지수': item.futures_3y if item.futures_3y else item.bond_3y, # Proxy
                '10년국채선물지수': item.futures_10y if item.futures_10y else item.bond_10y, # Proxy
                '최근월물 CALL ATM': item.call_atm if item.call_atm else 1.0, # Avoid div/0
                '최근월물 PUT ATM': item.put_atm if item.put_atm else 1.0
            })
            
        df = pd.DataFrame(data_list)
        df = df.sort_values('Date').reset_index(drop=True)
        
        # 2. Process KOSPI
        if '코스피' in df.columns:
            k = df.copy()
            k = calculate_rsi(k, '코스피')
            k = calculate_fear_greed(k, '코스피', '코스피 200 변동성지수', '최근월물 CALL ATM', '최근월물 PUT ATM', '5년 국채선물 추종 지수', '10년국채선물지수')
            k = calculate_macd(k, 'Fear_Greed_Index')
            k = add_super_ma_gap(k, '코스피', 'KOSPI')
            k = add_impulse_components(k, '코스피', 'KOSPI')
            k = add_td_setup_counts(k, '코스피', 'TD')
            
            # Slice recent for plotting
            k_recent = k[k['Date'] >= k['Date'].max() - pd.DateOffset(months=6)]
            
            if not k_recent.empty:
                # F&G Chart
                if 'Oscillator' in k_recent.columns:
                    img_fg = plot_fg(k_recent, '코스피', 'KOSPI – Fear & Greed Oscillator')
                    results.append({'key':'k_fg', 'type':'image', 'title':'KOSPI F&G', 'data':img_fg, 'order':10})
                
                # Impulse Chart
                img_imp = plot_impulse_chart(k_recent, '코스피', 'KOSPI_EMA13', 'KOSPI_MACD_Hist', 'KOSPI – Impulse System')
                results.append({'key':'k_imp', 'type':'image', 'title':'KOSPI Impulse', 'data':img_imp, 'order':11})
                
                # DeMark Chart
                img_td = plot_demark_daily(k_recent, '코스피', 'KOSPI – DeMark TD')
                results.append({'key':'k_td', 'type':'image', 'title':'KOSPI DeMark', 'data':img_td, 'order':12})

        # 3. Process KOSDAQ
        if '코스닥' in df.columns:
            q = df.copy()
            q = calculate_rsi(q, '코스닥')
            q = calculate_fear_greed(q, '코스닥', '코스피 200 변동성지수', '최근월물 CALL ATM', '최근월물 PUT ATM', '5년 국채선물 추종 지수', '10년국채선물지수')
            q = calculate_macd(q, 'Fear_Greed_Index')
            q = add_super_ma_gap(q, '코스닥', 'KOSDAQ')
            q = add_impulse_components(q, '코스닥', 'KOSDAQ')
            q = add_td_setup_counts(q, '코스닥', 'TD')
            
            q_recent = q[q['Date'] >= q['Date'].max() - pd.DateOffset(months=6)]
            
            if not q_recent.empty:
                 if 'Oscillator' in q_recent.columns:
                    img_fg = plot_fg(q_recent, '코스닥', 'KOSDAQ – Fear & Greed Oscillator')
                    results.append({'key':'q_fg', 'type':'image', 'title':'KOSDAQ F&G', 'data':img_fg, 'order':20})
                 
                 img_imp = plot_impulse_chart(q_recent, '코스닥', 'KOSDAQ_EMA13', 'KOSDAQ_MACD_Hist', 'KOSDAQ – Impulse System')
                 results.append({'key':'q_imp', 'type':'image', 'title':'KOSDAQ Impulse', 'data':img_imp, 'order':21})
                 
                 img_td = plot_demark_daily(q_recent, '코스닥', 'KOSDAQ – DeMark TD')
                 results.append({'key':'q_td', 'type':'image', 'title':'KOSDAQ DeMark', 'data':img_td, 'order':22})

    except Exception as e:
        P.logger.error(f"Analysis Error: {e}")
        import traceback
        P.logger.error(traceback.format_exc())
        return [{'type': 'text', 'title': 'Analysis Error', 'data': str(e)}]
        
    return results
