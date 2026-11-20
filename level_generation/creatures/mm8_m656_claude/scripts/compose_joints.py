"""Compose the inspected Meshy proposal with the actual glove-cuff centres."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
proposal = json.loads((P/'work/meshy_joints.json').read_text())
j = proposal['joints']
j['R_Hand'] = [-0.4417, -0.0125, 0.9278]
j['L_Hand'] = [0.4389, -0.0121, 0.9260]
out = {'height_m': 1.7, 'joints': j, 'method': 'Meshy axial and limb proposal; wrists fitted to 14-edge open glove cuffs. Generic rings rejected because armour and boot cuffs confused them.'}
(P/'work/joints_final.json').write_text(json.dumps(out, indent=2))
