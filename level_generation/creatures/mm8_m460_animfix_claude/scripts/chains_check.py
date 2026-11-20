"""Compare dumped cloak chain rest points with a GLB's bind pose (chain bone heads), per chain; with --from-glb build
the chains from the GLB itself (heads of the four bones; the end joint along the last bone's axis to the farthest
vertex it dominates), with the chain angle from the bone name (Cloak_m15 -> -15) or the root's direction.

    chains_check.py <glb> <chains.json>             compare
    chains_check.py <glb> <out.json> --from-glb <prefix> [deg_from_name|deg_from_root]
"""
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

glb = glb_pose.Glb(sys.argv[1])
model = glb_pose.Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
joints = list(model.joints)
bind = {names[j]: np.linalg.inv(model.inverse_binds[i]) for i, j in enumerate(joints)}


def to_blender(p):
    return [float(p[0]), float(-p[2]), float(p[1])]


if '--from-glb' not in sys.argv:
    data = json.load(open(sys.argv[2]))
    worst = 0.0
    for c in data['chains']:
        P = np.array(c['pts'])
        glbp = np.array([[P[k][0], P[k][2], -P[k][1]] for k in range(5)])
        heads = np.array([bind[b][:3, 3] for b in c['bones']])
        d = np.linalg.norm(heads - glbp[:4], axis=1)
        worst = max(worst, float(d.max()))
    print('chains', len(data['chains']), 'max head distance (m)', round(worst, 5))
    sys.exit()

out, prefix = sys.argv[2], sys.argv[sys.argv.index('--from-glb') + 1]
groups = {}
for n in bind:
    m = re.match(rf'{prefix}(.+)_(\d)$', n)
    if m:
        groups.setdefault(m.group(1), {})[int(m.group(2))] = n
prim = model.primitives[0]
rest_points = prim['positions']
dom = prim['joints'][np.arange(len(rest_points)), np.argmax(prim['weights'], axis=1)]
dom_names = np.array([names[joints[j]] for j in dom])
chains = []
for tag, bones in groups.items():
    bones = [bones[k] for k in range(4)]
    heads = [bind[b][:3, 3] for b in bones]
    axis = bind[bones[3]][:3, :3] @ np.array([0, 1.0, 0])
    axis /= np.linalg.norm(axis)
    v = rest_points[dom_names == bones[3]]
    length = float(((v - heads[3]) @ axis).max()) if len(v) else float(np.linalg.norm(heads[3] - heads[2]))
    end = heads[3] + axis * length
    pts = [to_blender(p) for p in heads + [end]]
    root = heads[0]
    # the MM6 Sorcerer's robe_rig.py: Robe_NN at -180 + NN * 22.5 deg (rays from its axis); otherwise the root's
    deg = -180.0 + 22.5 * int(tag) if tag.isdigit() else float(np.degrees(np.arctan2(root[0], -root[2])))
    chains.append({'deg': deg, 'pts': pts, 'bones': bones, 'tag': tag})
chains.sort(key=lambda c: c['deg'])
json.dump({'chains': chains}, open(out, 'w'))
print('built', len(chains), [(c['tag'], round(c['deg'], 1)) for c in chains])
