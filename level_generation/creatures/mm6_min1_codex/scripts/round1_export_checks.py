import runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/trace_final.py'),init_globals={'INPUT':'export/mm6_min1.glb'})
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':'export/mm6_min1.glb','REPORT':'review/round1/export_acceleration_gate.json'})
assert json.loads((P/'review/round1/export_acceleration_gate.json').read_text())['pass']
runpy.run_path(str(P/'scripts/round1_export_pose.py'))
runpy.run_path(str(P/'scripts/render_final.py'))
