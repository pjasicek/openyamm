import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'finish_rig.py'),run_name='__main__')
sys.argv=['rig_gates.py','--','work/gated_master.blend'];runpy.run_path(str(P/'rig_gates.py'),run_name='__main__')
