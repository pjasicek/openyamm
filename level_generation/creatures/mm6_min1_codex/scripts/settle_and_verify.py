import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'settle_death.py'),run_name='__main__')
sys.argv=['rig_gates.py','--','work/gated_master.blend'];runpy.run_path(str(P/'rig_gates.py'),run_name='__main__')
runpy.run_path(str(P/'export_and_trace.py'),run_name='__main__')
