"""Share of faces whose normal points toward their chain's axis (inverted) per neck chain and the body; rest pose.
Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Body'].data
RJ = json.load(open(os.path.join(HERE, 'work', 'rig.json')))['chains']
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
own = np.zeros(len(me.vertices), int); me.attributes['chain_owner'].data.foreach_get('value', own)
for k in range(1, 6):
    J = np.array(RJ[k]['joints'])
    inv = tot = 0
    for p in me.polygons:
        if part[p.index] != 0 or np.bincount(own[list(p.vertices)], minlength=6).argmax() != k:
            continue
        c = np.array(p.center); best = None
        for a, b in zip(J[:-1], J[1:]):
            d = b - a; t = np.clip((c - a) @ d / (d @ d), 0, 1); q = a + t * d
            dist = np.linalg.norm(c - q)
            if best is None or dist < best[0]:
                best = (dist, q)
        tot += 1; inv += int(np.array(p.normal) @ (c - best[1]) < 0)
    print(f'NECK {k}: faces {tot}, inverted {inv} ({100 * inv / max(tot, 1):.0f} %)')
