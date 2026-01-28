# -*- coding: utf-8 -*-
from plugin import *
from .models import ModelStockRefHistory

setting = {
    'filepath': __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': 'analysis',
    'menu': {
        'uri': __package__,
        'name': '주식 연구',
        'list': [
            {
                'uri': 'analysis',
                'name': '분석',
                'list': [
                    {'uri': 'dashboard', 'name': 'KRX_Fear&Grid'},
                    {'uri': 'list', 'name': 'ETF 상대강도'},
                    {'uri': 'db_kr', 'name': '시장 데이터 (DB)'},
                ]
            },
            {
                'uri': 'base',
                'name': '설정',
                'list': [
                    {'uri': 'setting', 'name': '설정'},
                    {'uri': 'log', 'name': '로그'},
                ]
            }
        ]
    },
    'default_route': 'normal',
}

P = create_plugin_instance(setting)

try:
    from .presenters import ModuleBase, ModuleAnalysis
    
    P.set_module_list([ModuleBase, ModuleAnalysis])
    P.ModelSetting = P.ModelSetting
    
    # Auto-create table logic is handled by ModelBase usually.
    # We removed manual creation to rely on SQLAlchemy or just let it init on first usage if configured correctly.
    # Or strict v2 check if needed.
        
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    import traceback
    P.logger.error(traceback.format_exc())
