import sys,runpy
from pathlib import Path
sys.argv.append('--preview')
runpy.run_path(str(Path(__file__).with_name('round1_repair.py')),run_name='__main__')
