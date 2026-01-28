import sys
import subprocess

try:
    import yfinance
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', f'{__path__[0]}/requirements.txt'])
