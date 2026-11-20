from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
r=json.loads((p/'work/gates_runtime_round1.json').read_text())
assert len(r)==8
for name,g in r.items():
 assert all(g[k] for k in ['G4_pass','G5_pass','G6_pass']), (name,g)
 assert g['floor_min_mm']>=-2 and g['grip_min_mm']>=10.5,(name,g)
print('PASS: all eight exported clips, G4/G5/G6, floor and grip')
