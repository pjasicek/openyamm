import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
os.environ.pop('PENETRATION_PROBE',None)
for name in ['review3_sleeves.py','review3_walk_lift.py','review3_death_feet.py','review3_leg_weights.py','review3_floor.py','review3_arm_frames.py','review3_cast_timing.py','review3_penetration.py','review3_anatomy.py','review3_dense.py','review3_preview.py','review3_contacts.py']:
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')

import json
assert all(v['pass'] for v in json.loads((p/'review/round3/penetration.json').read_text())['clips'].values())
assert all(v[0]<=.2 for row in json.loads((p/'work/g6_contacts.json').read_text()).values() for v in row.values())
