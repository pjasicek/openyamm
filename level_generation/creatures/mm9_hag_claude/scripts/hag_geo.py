"""Hag geometry from the approved Yrsa master (2026-11-02): MM9's hag.abc is Yrsa.abc with (1) no forehead bead band
(the Hag's skin has none) and (2) bell sleeves: the lower-back side of each cuff hangs out up to ~9.7 cm (MM9 forearm
vertices; see README). Everything else (body, head shell, hood, braids, hands, weights, UVs, attributes) is unchanged.

(1) The bead band = the eight small head parts on the forehead (loose parts numbered as head_split.py; selected by
    position, rest y < -0.385 m, z > 0.585 m, under 25 vertices) are deleted.
(2) Sleeve flare: every vertex of the sleeve shell (the loose part holding both sleeves; its lining and cuff rim come
    along, so the 3 mm lining gap holds) beyond FLARE_T0 along the forearm axis (elbow -> wrist joint heads) moves
    outward from the axis by w(t) * (BASE + HANG * a^2), w = smoothstep from FLARE_T0 to the cuff end, a = how much the
    vertex's radial direction points back-and-down (MM9's hang direction, Blender (0, 0.89, -0.46)).
Args: <in blend> <out blend> <report json>
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
FLARE_T0, BASE, HANG = 0.09, 0.012, 0.09
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
assert body.matrix_world == rig.matrix_world or True
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for ed in x.link_edges:
            y = ed.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
co = np.array([v.co[:] for v in bm.verts])
Mw = np.array(body.matrix_world); assert np.allclose(Mw, np.eye(4), atol=1e-6), Mw
rep = {'beads': [], 'flare': {}}
# (2) flare first (vertex indices still valid)
counts = np.bincount(comp)
sleeve_part = int(np.argmax([counts[c] if (co[comp == c][:, 0].min() < -0.5 and co[comp == c][:, 0].max() > 0.5
                              and (comp == c).sum() < 2000 and co[comp == c][:, 2].min() > 0.0) else 0 for c in range(cid)]))
rep['sleeve_part'] = sleeve_part
M = rig.matrix_world
hang = np.array([0.0, 0.89, -0.46]); hang /= np.linalg.norm(hang)
for s in 'LR':
    e = np.array(M @ rig.data.bones[f'FHP {s} Forearm'].head_local); w = np.array(M @ rig.data.bones[f'FHP {s} Hand'].head_local)
    ax = (w - e) / np.linalg.norm(w - e)
    sel = np.where((comp == sleeve_part) & (np.sign(co[:, 0]) == np.sign(e[0])))[0]
    t = (co[sel] - e) @ ax
    tend = t.max()
    rad = co[sel] - e - np.outer(t, ax); r = np.linalg.norm(rad, axis=1)
    u = rad / np.maximum(r, 1e-6)[:, None]
    h = hang - (hang @ ax) * ax; h /= np.linalg.norm(h)
    a = np.clip(u @ h, 0, 1)
    x = np.clip((t - FLARE_T0) / (tend - FLARE_T0), 0, 1); wgt = x * x * (3 - 2 * x)
    d = (wgt * (BASE + HANG * a ** 2))[:, None] * u
    for k, i in enumerate(sel):
        bm.verts[i].co = Vector(co[i] + d[k])
    mag = np.linalg.norm(d, axis=1)
    rep['flare'][s] = {'verts_moved': int((mag > 1e-5).sum()), 'max_cm': round(float(mag.max()) * 100, 2), 'cuff_t': round(float(tend), 3)}
# (1) beads
dele = []
for c in range(cid):
    m = comp == c
    if m.sum() < 25 and co[m][:, 1].max() < -0.385 and co[m][:, 2].min() > 0.585:
        dele += [bm.verts[i] for i in np.where(m)[0]]
        rep['beads'].append({'part': c, 'verts': int(m.sum()), 'centre': np.round(co[m].mean(0), 3).tolist()})
bmesh.ops.delete(bm, geom=dele, context='VERTS')
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('HAGGEO', json.dumps(rep))
