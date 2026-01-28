# -*- coding: utf-8 -*-
# analyzers/etf_rs.py
import numpy as np
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    import yfinance as yf
except ImportError:
    yf = None

def analyze(P):
    """
    ETF Relative Strength Analysis
    """
    if yf is None:
        P.logger.error("yfinance module not found.")
        return None

    # 1. Define Data
    KOREA_INDUSTRY_ETFS = {
        "091170.KS": "KODEX 은행", "102970.KS": "KODEX 증권", "117700.KS": "KODEX 건설", 
        "300950.KS": "KODEX 게임산업", "091160.KS": "KODEX 반도체", "005930.KS": "삼성전자",
        "244580.KS": "KODEX 바이오", "228800.KS": "TIGER 여행레저", "091180.KS": "KODEX 자동차", 
        "305540.KS": "TIGER 2차전지테마", "228790.KS": "TIGER 화장품", "449450.KS": "PLUS K 방산"
    }
    tickers = list(KOREA_INDUSTRY_ETFS.keys())
    
    try:
        data = yf.download(tickers + ["^KS11"], period="6mo", interval="1d", progress=False, threads=False)["Close"]
    except Exception as e:
        P.logger.error(f"yfinance download failed: {e}")
        return None

    if data.empty:
        return None

    etf_data = data[tickers].copy()
    kospi = data["^KS11"].dropna()
    
    results = []
    for ticker in tickers:
        try:
            etf_series = etf_data[ticker].dropna()
            common_idx = etf_series.index.intersection(kospi.index)
            if len(common_idx) < 52: continue
            
            etf_series = etf_series.loc[common_idx]
            kospi_series = kospi.loc[common_idx]
            
            relative = etf_series / kospi_series
            if (kospi_series == 0).any(): continue

            ma = relative.rolling(window=52).mean() 
            rs = ((relative / ma) - 1) * 100
            latest_raw = rs.iloc[-1]
            norm_rs = 100 * (1 / (1 + np.exp(-latest_raw / 12)))
            
            results.append({
                'ticker': ticker,
                'name': KOREA_INDUSTRY_ETFS[ticker],
                'raw_rs': round(latest_raw, 2),
                'norm_rs': round(norm_rs, 2)
            })
        except:
            continue
            
    results.sort(key=lambda x: x['norm_rs'], reverse=True)
    
    # Generate Plot
    plot_b64 = ""
    if results:
        try:
            top10 = results[:8]
            names = [x['name'] for x in top10]
            values = [x['norm_rs'] for x in top10]
            
            plt.figure(figsize=(10, 5), dpi=100)
            plt.barh(names[::-1], values[::-1], color='skyblue')
            plt.xlabel('Normalized Mansfield RS')
            plt.title('Top ETF Relative Strength')
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            plot_b64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
        except Exception as e:
            P.logger.error(f"Plot error: {e}")

    # Return standard format
    return [
        {
            'key': 'etf_plot',
            'type': 'image',
            'title': 'ETF RS Ranking',
            'data': plot_b64,
            'order': 1
        },
        {
            'key': 'etf_table',
            'type': 'table', # Generic table renderer
            'title': 'ETF Analysis Details',
            'columns': ['순위', '이름', '티커', 'Normalized RS', 'Raw RS'],
            'data': results[:10], # Just top 10 for table
            'order': 3
        }
    ]
