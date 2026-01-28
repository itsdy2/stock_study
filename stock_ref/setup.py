# -*- coding: utf-8 -*-
from plugin import *
from .constants import OPTS

# Current file path setup
OPTS['filepath'] = __file__

# Plugin Initialization
P = create_plugin_instance(OPTS)
PLUGIN = P

try:
    from .presenters import ModuleBase, ModuleAnalysis
    
    P.set_module_list([ModuleBase, ModuleAnalysis])
    
    PluginModelSetting = P.ModelSetting

except Exception as e:
    P.logger.error(f'Exception:{str(e)}')
    P.logger.error(traceback.format_exc())
