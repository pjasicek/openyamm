#!/usr/bin/env python3
"""In-game poses round three friendly Ghosts over open water (isleofashes.odm): writes review/ingame_tour.yml, review/ghost_shots.yml. Args: output dir under review/, [hostile]"""
import math, sys, yaml
from pathlib import Path
P = Path(__file__).resolve().parents[1]
out = str(P / 'review' / sys.argv[1])
Path(out).mkdir(exist_ok=True)
x0, y0, z0 = -2500, 330, 170
def sh(n, px, py, pz, yaw, pitch=0.0):
    return {'name': n, 'position': [px, py, pz], 'yaw': yaw, 'pitch': pitch}
d = 480
shots = [sh('t_all', x0, y0 - 900, 330, math.pi / 2, 0.03)]
for tier, ox in (('b', 0), ('a', -300), ('c', 300)):
    for name, az in (('front', 0), ('q34', 40), ('side', 90), ('back', 180), ('sideb', -90)):
        a = math.radians(az)
        px = x0 + ox + d * math.sin(a); py = y0 - d * math.cos(a)
        shots.append(sh(f'{tier}_{name}', px, py, 330, math.atan2(y0 - py, x0 + ox - px), 0.02))
shots.append(sh('b_under', x0, y0 - 300, 130, math.pi / 2, -0.55))
yaml.safe_dump({'output_dir': out, 'exit': True, 'settle_seconds': 1.2, 'shots': shots}, open(P / 'review/ghost_shots.yml', 'w'), sort_keys=False)
st = [{'wait': 0.2}]
for m, ox in ((9138, -300), (9139, 0), (9140, 300)):
    st.append({'console': f'actor spawn {m} 1 {x0 + ox} {y0} {z0} friendly'})
yaml.safe_dump({'output_dir': out, 'exit': False, 'steps': st}, open(P / 'review/ingame_tour.yml', 'w'), sort_keys=False)
print(len(shots), 'shots')
