"""Print a GLB's clips (name, duration) and joint names. Args: <glb>"""
import sys, json, struct
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
import glb_pose
g = glb_pose.Glb(sys.argv[1])
J = g.json
for a in J.get('animations', []):
    tmax = 0.0
    for s in a['samplers']:
        acc = J['accessors'][s['input']]
        tmax = max(tmax, acc.get('max', [0])[0])
    print('clip', a['name'], round(tmax, 4))
skin = J['skins'][0]
print('joints', len(skin['joints']), [J['nodes'][i]['name'] for i in skin['joints']])
print('meshes', [m.get('name') for m in J['meshes']])
