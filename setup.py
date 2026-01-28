# -*- coding: utf-8 -*-
import traceback
from plugin import *

# 1. Plugin Setup
setting = {
    'filepath': __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': 'base', 
    'menu': {
        'uri': __package__,
        'name': '주식 투자 참고',
        'list': [
            {
                'uri': 'base',
                'name': '설정',
                'list': [
                    {'uri': 'setting', 'name': '기본 설정'},
                ]
            },
            {
                'uri': 'analysis',
                'name': '분석',
                'list': [
                    {'uri': 'dashboard', 'name': '대시보드'},
                    {'uri': 'list', 'name': 'ETF 상대강도'},
                ]
            }
        ]
    },
    'default_route': 'normal',
}

# 2. Create Plugin Instance
P = create_plugin_instance(setting)

try:
    # 3. Define ModelSetting
    PluginModelSetting = P.ModelSetting

    # 4. Import and Register Modules
    from .presenters import ModuleBase, ModuleAnalysis
    from .models import ModelStockRefHistory 
    
    P.set_module_list([ModuleBase, ModuleAnalysis])
    
except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())
