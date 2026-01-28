# -*- coding: utf-8 -*-
from plugin import *

setting = {
    'filepath': __file__,
    'use_db': True,
    'use_default_setting': True,
    'home_module': 'analysis',
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

P = create_plugin_instance(setting)

try:
    from .mod_base import ModuleBase
    from .mod_analysis import ModuleAnalysis
    
    P.set_module_list([ModuleBase, ModuleAnalysis])
    
    PluginModelSetting = P.ModelSetting

except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())
