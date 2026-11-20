"""Edge stretch per clip (Blender, 48 Hz): posed/rest edge length ratio, p99.9 and max, per v3 part (0 cdr1 body,
1 head, 2 neck loft, 3 spines) and for the seam band (edges within two rings of the loft). Usage:
blender -b <blend> -P stretch_gate.py -- <out.json>"""
import bpy, json, sys
import numpy as np
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; sc = bpy.context.scene; me = o.data
E = np.empty(len(me.edges) * 2, np.int64); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
part = np.array([d.value for d in me.attributes['v3part'].data])
rest = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1); ok = L0 > 1e-5
ep = np.maximum(part[E[:, 0]], part[E[:, 1]]); ep[(part[E[:, 0]] == 2) | (part[E[:, 1]] == 2)] = 2
seam = np.zeros(len(rest), bool); seam[part == 2] = True
for _ in range(2):
    s2 = seam.copy(); s2[E[seam[E[:, 0]], 1]] = True; s2[E[seam[E[:, 1]], 0]] = True; seam = s2
eseam = seam[E[:, 0]] & seam[E[:, 1]]
res = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; R = []
    for k in range(int((f1 - f0) * 2) + 1):
        fr = f0 + k * .5; sc.frame_set(int(fr), subframe=fr % 1)
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        c = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', c); c = c.reshape(-1, 3); ev.to_mesh_clear()
        R.append(np.linalg.norm(c[E[:, 0]] - c[E[:, 1]], axis=1) / np.maximum(L0, 1e-9))
    R = np.array(R)[:, ok]; r = {}
    for name, sel in [('body', ep[ok] == 0), ('head', ep[ok] == 1), ('loft', ep[ok] == 2), ('spines', ep[ok] == 3), ('seam_band', eseam[ok])]:
        x = R[:, sel]
        if x.size == 0: continue
        r[name] = {'p99.9': round(float(np.percentile(np.maximum(x, 1 / x), 99.9)), 3), 'max': round(float(np.maximum(x, 1 / x).max()), 3)}
    res[act.name] = r
json.dump(res, open(out, 'w'), indent=1); print('STRETCH', json.dumps({k: {n: x['p99.9'] for n, x in v.items()} for k, v in res.items()}))
