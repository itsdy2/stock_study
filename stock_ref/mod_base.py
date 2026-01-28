# -*- coding: utf-8 -*-
from plugin import PluginModuleBase
from flask import render_template
from .setup import P

class ModuleBase(PluginModuleBase):
    def __init__(self, P):
        super(ModuleBase, self).__init__(P, name='base', first_menu='setting')
        self.db_default = {
            'analysis_interval': '30 8 * * *', # 매일 아침 8시 30분
            'auto_analysis': 'False',
            'telegram_token': '',
            'telegram_chat_id': '',
            'db_retention_days': '365', 
        }

    def process_menu(self, page, req):
        try:
            arg = P.ModelSetting.to_dict()
            return render_template(
                f'{P.package_name}_{self.name}_{page}.html',
                arg=arg
            )
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return "Error"
    
    def setting_save_after(self, change_list):
        if 'analysis_interval' in change_list or 'auto_analysis' in change_list:
             from .mod_analysis import ModuleAnalysis
             P.logic.scheduler_stop(ModuleAnalysis.name)
             P.logic.scheduler_start(ModuleAnalysis.name)

