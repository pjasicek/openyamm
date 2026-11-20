import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/probe_final.py'),run_name='__main__')
sys.argv=['stride.py','--',str(P/'work/gated_master.blend'),'Walking','Running'];runpy.run_path(str(P/'scripts/stride.py'),run_name='__main__')
