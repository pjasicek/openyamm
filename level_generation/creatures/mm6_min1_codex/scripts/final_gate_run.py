import runpy,sys
from pathlib import Path
S=Path(__file__).resolve().parent
for n in ['bake_subframes.py','smooth_final_weights.py','elbow_gate.py']:
 runpy.run_path(str(S/n),run_name='__main__')
sys.argv=['rig_gates_48.py','--','work/final_master.blend'];runpy.run_path(str(S/'rig_gates_48.py'),run_name='__main__')
