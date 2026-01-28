# -*- coding: utf-8 -*-
from plugin import ModelBase, F
from sqlalchemy import Column, Integer, String, DateTime, Text, desc
from datetime import datetime
import traceback
import json

class ModelStockRefHistory(ModelBase):
    __tablename__ = 'stock_study_history'
    __bind_key__ = 'stock_study'

    id = Column(Integer, primary_key=True)
    created_time = Column(DateTime, default=datetime.now)
    data_json = Column(Text) # JSON data for dashboard
    image_b64 = Column(Text) # Legacy, keeping for compatibility
    
    def __init__(self, data_json, image_b64):
        self.data_json = data_json
        self.image_b64 = image_b64
        self.created_time = datetime.now()
        
    def save(self):
        try:
            with F.app.app_context():
                F.db.session.add(self)
                F.db.session.commit()
        except Exception as e:
            from .setup import P
            P.logger.error(f'Exception:{str(e)}')

    @classmethod
    def get_list(cls, by_dict=False):
        try:
            with F.app.app_context():
                query = F.db.session.query(cls).order_by(desc(cls.id))
                return query.all()
        except Exception as e:
            from .setup import P
            P.logger.error(f'Exception:{str(e)}')
            return []

    @classmethod
    def get_last(cls):
        try:
            with F.app.app_context():
                query = F.db.session.query(cls).order_by(desc(cls.id)).limit(1)
                return query.first()
        except Exception as e:
            from .setup import P
            P.logger.error(f'Exception:{str(e)}')
            return None

    @classmethod
    def delete_older_than(cls, days):
        try:
            from datetime import timedelta
            limit_date = datetime.now() - timedelta(days=int(days))
            with F.app.app_context():
                count = F.db.session.query(cls).filter(cls.created_time < limit_date).delete()
                F.db.session.commit()
                from .setup import P
                P.logger.info(f"Deleted {count} old records (older than {days} days)")
        except Exception as e:
            from .setup import P
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())

class ModelKoreanMarket(ModelBase):
    __tablename__ = 'stock_study_kr_market'
    __bind_key__ = 'stock_study'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True) # YYYY-MM-DD
    
    kospi = Column(ModelBase.db.Float)
    kosdaq = Column(ModelBase.db.Float)
    vix = Column(ModelBase.db.Float) # KOSPI 200 Volatility
    
    bond_3y = Column(ModelBase.db.Float) # Yield
    bond_10y = Column(ModelBase.db.Float) # Yield
    
    # Placeholder for future
    individual_buy = Column(ModelBase.db.Float)
    foreigner_buy = Column(ModelBase.db.Float)
    institution_buy = Column(ModelBase.db.Float)
    
    created_time = Column(DateTime, default=datetime.now)

    def __init__(self, date_obj):
        self.date = date_obj
        self.created_time = datetime.now()

    @classmethod
    def get_data_by_days(cls, days=365):
        try:
            from datetime import timedelta
            start_date = datetime.now() - timedelta(days=days)
            with F.app.app_context():
                # Return dataframe friendly list of dicts?
                items = F.db.session.query(cls).filter(cls.date >= start_date).order_by(cls.date.asc()).all()
                return items
        except Exception as e:
            from .setup import P
            P.logger.error(f"DB Get Failed: {e}")
            return []
    
    def save(self):
        try:
            with F.app.app_context():
                F.db.session.add(self)
                F.db.session.commit()
        except Exception as e:
            # If unique constraint violation, update?
            from .setup import P
            P.logger.error(f"Save Market Data Failed: {e}")
