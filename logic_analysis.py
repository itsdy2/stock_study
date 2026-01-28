# -*- coding: utf-8 -*-
import os
import datetime
import traceback
import json
import importlib
import pkgutil

try:
    import yfinance as yf
except ImportError:
    yf = None

from .setup import P

class LogicAnalysis:
    
    @staticmethod
    def process_all():
        """
        Dynamically load and run all scripts in 'analyzers/' folder.
        """
        P.logger.info("Starting Modular Analysis...")
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        results_list = []
        
        # 1. Discover modules in 'analyzers' package
        import stock_study.analyzers as analyzer_pkg
        package_path = analyzer_pkg.__path__
        
        for loader, module_name, is_pkg in pkgutil.iter_modules(package_path):
            try:
                # Import module
                full_module_name = f'stock_study.analyzers.{module_name}'
                start_mod_time = datetime.datetime.now()
                P.logger.debug(f"Running analyzer: {module_name}")
                
                module = importlib.import_module(full_module_name)
                importlib.reload(module) # Reload to ensure fresh code execution if file changed
                
                # Check for 'analyze' function
                if hasattr(module, 'analyze'):
                    res = module.analyze(P)
                    
                    if res:
                        # Normalize result to list of items (one script can return multiple blocks)
                        if isinstance(res, list):
                            results_list.extend(res)
                        else:
                            results_list.append(res)
                
            except Exception as e:
                P.logger.error(f"Error running analyzer {module_name}: {str(e)}")
                P.logger.error(traceback.format_exc())

        # 2. Sort results by 'order'
        results_list.sort(key=lambda x: x.get('order', 99))
        
        # 3. Save to DB
        data_to_save = {
            'results': results_list,
            'updated_time': current_time,
        }
        
        # (Legacy Notifications Logic - Simplification for now)
        # We can implement a generic notification check if the analyzer returns 'alert': True
        
        try:
            from .models import ModelStockRefHistory
            # We don't store separate image_b64 anymore, everything is in data_json
            item = ModelStockRefHistory(json.dumps(data_to_save), "") 
            item.save()
            
            # Pruning
            retention_days = P.ModelSetting.get('db_retention_days')
            ModelStockRefHistory.delete_older_than(retention_days)
            
            P.logger.info("Analysis Completed & Saved.")
            
        except Exception as e:
            P.logger.error(f"DB Save Failed: {str(e)}")

    @staticmethod
    def get_dashboard_data():
        from .models import ModelStockRefHistory
        last = ModelStockRefHistory.get_last()
        if last:
            try:
                data = json.loads(last.data_json)
                return data
            except:
                return None
        return None
