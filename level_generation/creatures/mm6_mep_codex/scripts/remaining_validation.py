import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for script in ['actual_grip_gate.py','export_trace_final.py','acceleration_gate.py','final_visual_metrics.py','render_final.py']:
 runpy.run_path(str(p/'scripts'/script),run_name='__main__')
