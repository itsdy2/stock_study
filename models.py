# -*- coding: utf-8 -*-
from plugin import ModelBase, F
from sqlalchemy import Column, Integer, String, DateTime, Text, desc
from datetime import datetime
from .setup import P

class ModelStockRefHistory(ModelBase):
    __tablename__ = f'{P.package_name}_history'
    __bind_key__ = P.package_name

    id = Column(Integer, primary_key=True)
    created_time = Column(DateTime, default=datetime.now)
    data_json = Column(Text) # JSON string of analysis results
    image_b64 = Column(Text) # Base64 string of plot (optional or combined)
    
    def __init__(self, data_json, image_b64=None):
        self.data_json = data_json
        self.image_b64 = image_b64

    @classmethod
    def get_list(cls, by_dict=False):
        try:
            with F.app.app_context():
                query = F.db.session.query(cls).order_by(desc(cls.id))
                return query.all()
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            return []

    @classmethod
    def get_last(cls):
        try:
            with F.app.app_context():
                query = F.db.session.query(cls).order_by(desc(cls.id)).limit(1)
                return query.first()
        except Exception as e:
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
                P.logger.info(f"Deleted {count} old records (older than {days} days)")
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
