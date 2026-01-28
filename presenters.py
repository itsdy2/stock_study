# -*- coding: utf-8 -*-
from plugin import PluginModuleBase, F
from flask import render_template, jsonify
from .setup import P
from .logic_analysis import LogicAnalysis

class ModuleBase(PluginModuleBase):
    def __init__(self, P):
        super(ModuleBase, self).__init__(P, name='base', first_menu='setting')
        self.db_default = {
            'analysis_interval': '30 8 * * *', 
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
             P.logic.scheduler_stop('analysis') 
             P.logic.scheduler_start('analysis')

class ModuleAnalysis(PluginModuleBase):
    def __init__(self, P):
        super(ModuleAnalysis, self).__init__(P, name='analysis', first_menu='dashboard')
        self.set_page_list([]) 

    def process_menu(self, page, req):
        try:
            arg = P.ModelSetting.to_dict()
            if page == 'dashboard':
                data = LogicAnalysis.get_dashboard_data()
                return render_template(
                    f'{P.package_name}_{self.name}_{page}.html',
                    arg=arg, data=data
                )
            elif page == 'list':
                data = LogicAnalysis.get_dashboard_data()
                return render_template(
                    f'{P.package_name}_{self.name}_{page}.html',
                    arg=arg, data=data
                )
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            P.logger.error(traceback.format_exc())
            return "Error"
            
    def process_ajax(self, sub, req):
        try:
            if sub == 'run_analysis':
                LogicAnalysis.process_all()
                return jsonify({'ret':'success', 'msg':'분석 완료'})
        except Exception as e:
            P.logger.error(f'Exception:{str(e)}')
            return jsonify({'ret':'error', 'msg':str(e)})

    def scheduler_function(self):
        if P.ModelSetting.get_bool('auto_analysis'):
            LogicAnalysis.process_all()
