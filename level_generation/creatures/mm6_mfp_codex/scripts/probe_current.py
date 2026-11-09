import os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['GATE_RENDER']='0'
runpy.run_path(str(P/'scripts/initial_checks.py'),run_name='__main__')
