"""Pull the grafted hand stub's stray flap back onto the wrist (graft_hands.py conformed one stub vertex per wrist to a
far hit of its ray cast, a 2-3 cm triangle hanging below the wrist ring). Hand-stub
vertices (on grafted hand faces only) along the forearm -> hand axis at s = -0.10..+0.03 m from the hand joint whose distance
from the axis exceeds 1.25 x the band's median radius (1.5 cm bands) are pulled radially to it. Positions only.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
ok = np.array([len(v.link_faces) > 0 and all(f[lh] != 0 for f in v.link_faces) for v in bm.verts])
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    rel = CO - a1; s = rel @ ax; perp = rel - np.outer(s, ax); r = np.linalg.norm(perp, axis=1)
    sel = ok & (s > -0.10) & (s < 0.03) & (r < 0.08)
    n = 0
    for b0 in np.arange(-0.10, 0.03, 0.015):
        m = sel & (s >= b0) & (s < b0 + 0.015)
        if m.sum() < 4: continue
        med = np.median(r[m])
        for i in np.nonzero(m & (r > 1.25 * med))[0]:
            p = a1 + s[i] * ax + perp[i] / r[i] * 1.0 * med
            bm.verts[i].co = mwi @ __import__('mathutils').Vector(p.tolist()); n += 1
    # v2 (sleeve_poke_gate: 7 left stub vertices 20 mm outside the ring at rest): every stub vertex before the ring's
    # end (s < -0.02) stays inside the trimmed forearm ring: radius capped at the ring's median radius - 3 mm
    body_v = np.array([len(v.link_faces) > 0 and all(f[lh] == 0 and f[lk] == 0 for f in v.link_faces) for v in bm.verts])
    ring = body_v & (s > -0.045) & (s < -0.025) & (r < 0.08)
    if ring.sum() > 3:
        rr = np.median(r[ring]) - 0.003
        CO2 = np.array([tuple(mw @ v.co) for v in bm.verts]); rel2 = CO2 - a1; s2 = rel2 @ ax
        perp2 = rel2 - np.outer(s2, ax); r2 = np.linalg.norm(perp2, axis=1)
        for i in np.nonzero(ok & (s2 > -0.08) & (s2 < -0.02) & (r2 > rr) & (r2 < 0.08))[0]:
            p = a1 + s2[i] * ax + perp2[i] / r2[i] * rr
            bm.verts[i].co = mwi @ __import__('mathutils').Vector(p.tolist()); n += 1
    rep[tok] = n
bm.to_mesh(me); me.update()
print('WRISTCLAMP', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
