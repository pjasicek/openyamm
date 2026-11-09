import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['gate','--','work/round1_fitted.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
