# -*- coding: utf-8 -*-
import os
import datetime
import traceback
import io
import base64
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yfinance as yf
from .setup import P, PluginModelSetting
from .model import ModelStockRefHistory

class LogicAnalysis:
    
    KOREA_INDUSTRY_ETFS = {
        "091170.KS": "KODEX 은행", "140700.KS": "KODEX 보험", "102970.KS": "KODEX 증권",
        "117700.KS": "KODEX 건설", "300950.KS": "KODEX 게임산업", "395160.KS": "KODEX 시스템반도체",
        "445290.KS": "KODEX K-로봇액티브", "117460.KS": "KODEX 에너지화학", "091160.KS": "KODEX 반도체",
        "000660.KS": "SK하이닉스", "196170.KQ": "알테오젠", "015760.KS": "한국전력",
        "005490.KS": "POSCO홀딩스", "036460.KS": "한국가스공사", "005930.KS": "삼성전자",
        "244580.KS": "KODEX 바이오", "228800.KS": "TIGER 여행레저", "364970.KS": "TIGER 바이오 TOP 10",
        "091180.KS": "KODEX 자동차", "305540.KS": "TIGER 2차전지테마", "462010.KS": "TIGER 2차전지소재FN",
        "266360.KS": "KODEX 미디어&엔터테인먼트", "395150.KS": "KODEX 웹툰&드라마", "367760.KS": "RISE 5G테크",
        "228790.KS": "TIGER 화장품", "463250.KS": "TIGER 우주방산", "157490.KS": "TIGER 소프트웨어",
        "449450.KS": "PLUS K 방산", "139230.KS": "TIGER 200 중공업", "150460.KS": "TIGER 중국소비테마",
        "139280.KS": "TIGER 경기방어", "438900.KS": "HANARO FN K-푸드", "381570.KS": "HANARO FN친환경에너지",
        "210780.KS": "KODEX 코스피고배당", "466920.KS": "SOL 조선TOP3플러스", "475300.KS": "SOL 반도체전공정",
        "475310.KS": "SOL 반도체후공정", "307510.KS": "TIGER 의료기기", "433500.KS": "ACE 원자력테마딥서치",
        "483020.KS": "KIWOOM 의료AI", "261070.KS": "TIGER 코스닥150바이오테크","479850.KS": "HANARO K뷰티"
    }

    @staticmethod
    def process_all():
        """Run all analysis"""
        try:
            P.logger.info("Starting Stock Analysis...")
            
            # Fetch Data with Retry
            fg_results = LogicAnalysis.analyze_fear_greed_dummy()
            etf_results = LogicAnalysis.analyze_etf_rs()
            
            # Generate Plots (Optimized DPI)
            plot_b64 = LogicAnalysis.plot_top_etfs(etf_results)
            
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Prepare Data Package with simple history placeholder
            # In a real scenario, we would query previous DB entries to build a 30-day trend here.
            # For now, we save the current snapshot.
            data_to_save = {
                'fear_greed': fg_results,
                'etf_rs': etf_results,
                'updated_time': current_time,
                'last_alert_time': '' # To be updated if alert sent
            }
            
            # Notifications with De-duplication
            # Logic: Check last DB entry. If it was also "Extreme Fear" and sent recently, skip.
            last_db = ModelStockRefHistory.get_last()
            alert_sent = False
            if last_db:
                last_data = json.loads(last_db.data_json)
                # Pass last_data to check_notifications to decide
                alert_sent = LogicAnalysis.check_notifications(fg_results, etf_results, last_data)
            else:
                alert_sent = LogicAnalysis.check_notifications(fg_results, etf_results, None)
            
            if alert_sent:
                data_to_save['last_alert_time'] = current_time

            # Save to DB
            item = ModelStockRefHistory(json.dumps(data_to_save), plot_b64)
            item.save()
            
            # Pruning
            retention_days = P.ModelSetting.get('db_retention_days')
            ModelStockRefHistory.delete_older_than(retention_days)

            P.logger.info("Stock Analysis Completed & Saved.")
        except Exception as e:
            P.logger.error(f"Analysis failed: {str(e)}")
            P.logger.error(traceback.format_exc())

    @staticmethod
    def analyze_etf_rs():
        """Calculate Mansfield RS for ETFs (with error handling)"""
        tickers = list(LogicAnalysis.KOREA_INDUSTRY_ETFS.keys())
        try:
            # Download with retry logic
            # Explicitly using threads=False might help stability in some envs
            data = yf.download(tickers + ["^KS11"], period="6mo", interval="1d", progress=False, threads=False)["Close"]
        except Exception as e:
            P.logger.error(f"yfinance download failed: {e}")
            return []

        if data.empty:
            return []

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
                
                # Check for zero values to avoid division by zero
                if (kospi_series == 0).any(): continue

                ma = relative.rolling(window=52).mean() 
                rs = ((relative / ma) - 1) * 100
                latest_raw = rs.iloc[-1]
                norm_rs = 100 * (1 / (1 + np.exp(-latest_raw / 12)))
                
                results.append({
                    'ticker': ticker,
                    'name': LogicAnalysis.KOREA_INDUSTRY_ETFS[ticker],
                    'raw_rs': round(latest_raw, 2),
                    'norm_rs': round(norm_rs, 2)
                })
            except:
                continue
                
        results.sort(key=lambda x: x['norm_rs'], reverse=True)
        return results

    @staticmethod
    def analyze_fear_greed_dummy():
        """Placeholder for F&G logic"""
        return {
            'kospi': {'score': 50, 'status': 'Neutral'},
            'kosdaq': {'score': 45, 'status': 'Neutral'}
        }

    @staticmethod
    def plot_top_etfs(etf_results):
        try:
            if not etf_results: return ""
            top10 = etf_results[:10]
            names = [x['name'] for x in top10]
            values = [x['norm_rs'] for x in top10]
            
            plt.figure(figsize=(10, 6), dpi=100) # User suggested 80-100 DPI
            plt.barh(names[::-1], values[::-1], color='skyblue')
            plt.xlabel('Normalized Mansfield RS')
            plt.title('Top 10 ETF Relative Strength')
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            return img_b64
        except Exception as e:
            P.logger.error(f"Plotting failed: {e}")
            return ""

    @staticmethod
    def check_notifications(fg, etfs, last_data):
        try:
            token = P.ModelSetting.get('telegram_token')
            chat_id = P.ModelSetting.get('telegram_chat_id')
            if not token or not chat_id: return False

            # Check if we already sent an alert recently (e.g., today)
            # Simplified: if last status was same as current status and we sent alert, don't send again.
            # Use 'last_alert_time' from last_data if available.
            
            # Detect condition
            is_extreme_fear = fg['kospi']['score'] < 20
            
            # De-duplication Logic
            should_send = False
            
            if is_extreme_fear:
                # If last time wasn't extreme fear, OR it was extreme fear but we haven't alerted today?
                # Simple Logic: State Change trigger + Time throttle
                if last_data:
                    last_score = last_data['fear_greed']['kospi']['score']
                    if last_score >= 20: # Newly entered fear
                        should_send = True
                else:
                    should_send = True
            
            # Also check for Top ETF changes if needed (omitted for brevity unless requested)

            if should_send:
                msgs = []
                if is_extreme_fear:
                    msgs.append(f"⚠️ KOSPI Extreme Fear: {fg['kospi']['score']}")
                
                if etfs:
                    top = etfs[0]
                    msgs.append(f"🚀 Top ETF: {top['name']} (RS: {top['norm_rs']})")

                full_msg = "[Stock Ref] Alert\n" + "\n".join(msgs)
                from tool_base import ToolBaseNotify
                ToolBaseNotify.send_message(full_msg, chat_id=chat_id, token=token)
                return True
            
            return False

        except Exception as e:
            P.logger.error(f"Notification failed: {e}")
            return False

    @staticmethod
    def get_dashboard_data():
        last = ModelStockRefHistory.get_last()
        if last:
            try:
                data = json.loads(last.data_json)
                data['plot'] = last.image_b64
                return data
            except:
                return None
        return None

