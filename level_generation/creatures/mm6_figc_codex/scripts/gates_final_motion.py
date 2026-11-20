import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/motion_finish.py'),run_name='__main__')
sys.argv=['full_gates.py','--',str(P/'work/final_motion.blend')];runpy.run_path(str(P/'scripts/full_gates.py'),run_name='__main__')
