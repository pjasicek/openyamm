import runpy,sys
from pathlib import Path
S=Path(__file__).resolve().parent
runpy.run_path(str(S/'final_anatomy.py'),run_name='__main__')
runpy.run_path(str(S/'elbow_gate.py'),run_name='__main__')
sys.argv=['rig_gates.py','--','work/final_anatomy.blend'];runpy.run_path(str(S/'rig_gates.py'),run_name='__main__')
