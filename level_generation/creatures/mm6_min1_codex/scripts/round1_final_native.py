import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['gate','--','work/production_master.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'))
runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':'work/production_master.blend'})
runpy.run_path(str(P/'scripts/round1_acceleration.py'),init_globals={'INPUT':'work/production_master.blend'})
assert json.loads((P/'review/round1/acceleration_gate.json').read_text())['pass']
runpy.run_path(str(P/'scripts/elbow_gate.py'))
runpy.run_path(str(P/'scripts/final_blade_gate.py'))
assert all(all(v['pass'].values()) for v in json.loads((P/'review/rig_gates.json').read_text()).values())
assert all(v['pass'] for v in json.loads((P/'review/round1/precision_gate.json').read_text()).values())
runpy.run_path(str(P/'scripts/export_runtime.py'))
runpy.run_path(str(P/'scripts/round1_geometry_lods.py'))
