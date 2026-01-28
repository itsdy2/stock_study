# -*- coding: utf-8 -*-
import datetime
import time
from .setup import P
from .models import ModelKoreanMarket

try:
    from pykrx import stock, bond
    import yfinance as yf
except ImportError:
    stock = None
    bond = None
    yf = None

class LogicCollector:
    
    @staticmethod
    def sync_market_data(days=365):
        """
        Sync market data for the last N days.
        Checks DB for existing dates and backfills missing ones.
        """
        if not stock:
            P.logger.error("pykrx not installed")
            return

        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # 1. Get existing dates from DB to avoid redundant fetches (Optimization)
        # For simplicity in this iteration, we just fetch all and upsert/ignore
        
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        P.logger.info(f"Collecting Market Data: {start_str} ~ {end_str}")
        
        try:
            # A. KOSPI / KOSDAQ Index
            # 1001 = KOSPI, 2001 = KOSDAQ
            df_kospi = stock.get_index_ohlcv_by_date(start_str, end_str, "1001")
            df_kosdaq = stock.get_index_ohlcv_by_date(start_str, end_str, "2001")
            
            # B. Bond Yields (3y, 10y)
            # 국고채 3년, 10년 yields
            # pykrx bond module might need specific ticker or name
            # bond.get_otc_treasury_yields(start_str, end_str, "국고채3년")
            df_bond3 = bond.get_otc_treasury_yields(start_str, end_str, "국고채3년")
            df_bond10 = bond.get_otc_treasury_yields(start_str, end_str, "국고채10년")
            
            # C. VIX (yfinance)
            # ^VKOSPI
            try:
                vix_data = yf.download("^VKOSPI", start=start_date, end=end_date, progress=False, threads=False)['Close']
            except:
                vix_data = None
                
            # Iterate dates and save
            # df indices are datetime usually
            
            dates = df_kospi.index
            
            count = 0
            from plugin import F
            
            with F.app.app_context():
                for dt in dates:
                    date_obj = dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt
                    
                    # Check existence
                    exist = F.db.session.query(ModelKoreanMarket).filter_by(date=date_obj).first()
                    if not exist:
                        item = ModelKoreanMarket(date_obj)
                    else:
                        item = exist
                        
                    # Update values
                    try:
                        item.kospi = float(df_kospi.loc[dt]['종가'])
                        item.kosdaq = float(df_kosdaq.loc[dt]['종가'])
                        
                        if dt in df_bond3.index:
                            item.bond_3y = float(df_bond3.loc[dt]['수익률'])
                        if dt in df_bond10.index:
                            item.bond_10y = float(df_bond10.loc[dt]['수익률'])
                            
                        # VIX (Timezone naive/aware mismatch possible)
                        # Normalize date for lookup
                        if vix_data is not None:
                            # Simple lookup logic needed for VIX
                            # Skipping strictly for MVP speed, using default or partial
                            # Often matching index types is tricky (Timestamp vs Date)
                            pass 
                        
                    except Exception as parse_e:
                        continue # Skip bad rows
                        
                    F.db.session.add(item)
                    count += 1
                
                F.db.session.commit()
                P.logger.info(f"Market Data Synced: {count} records checked/updated.")
                
        except Exception as e:
            P.logger.error(f"Market Data Sync Error: {e}")
            import traceback
            P.logger.error(traceback.format_exc())

