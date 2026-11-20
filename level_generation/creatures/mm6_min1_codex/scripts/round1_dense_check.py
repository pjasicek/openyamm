import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_dense.py'),run_name='__main__',init_globals={'INPUT':'work/round1_relaxed.blend'})
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__')
sys.argv=['gate','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
