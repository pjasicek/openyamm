import runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
for script in ['author_cast.py','repair_elbow_frames.py','export_check.py','export_gates.py','cast_gate.py','ranged_gate.py','grip_export.py']:
 runpy.run_path(str(P/'scripts'/script),run_name='__main__')
print('CAST_EXPORT_GATES_COMPLETE')
