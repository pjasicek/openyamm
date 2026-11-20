"""Pull hand-stub outliers back inside the forearm (HOF2 sleeve_poke_gate: 2 right-stub vertices 22 mm outside the
forearm at rest). Per side, rest pose: hand-face vertices with s (along forearm -> hand from the hand joint) in
S0..0 whose radius from the forearm axis exceeds the body forearm surface's 90th-percentile radius in the same 1.5 cm band
are moved radially to 0.9 x that band's median body radius. Positions only. Args: <in blend> <out blend> [s0 -0.12]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
S0 = float(a[2]) if len(a) > 2 else -0.12
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
CO = np.array([tuple(mw @ v.co) for v in bm.verts])
hand = np.array([len(v.link_faces) > 0 and any(f[lh] != 0 for f in v.link_faces) for v in bm.verts])
bodyv = np.array([len(v.link_faces) > 0 and all(f[lh] == 0 and f[lk] == 0 for f in v.link_faces) for v in bm.verts])
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    rel = CO - a1; s = rel @ ax; perp = rel - np.outer(s, ax); r = np.linalg.norm(perp, axis=1)
    moved = []
    for b0 in np.arange(S0, 0.0, 0.015):
        bm_ = bodyv & (s >= b0 - 0.01) & (s < b0 + 0.025) & (r < 0.09)
        if bm_.sum() < 4: continue
        rmax = float(__import__('os').environ.get('RK', '1.0')) * np.percentile(r[bm_], float(__import__('os').environ.get('RP', '90'))); med = np.median(r[bm_])
        for i in np.nonzero(hand & (s >= b0) & (s < b0 + 0.015) & (r > rmax))[0]:
            p = a1 + s[i] * ax + perp[i] / r[i] * 0.9 * med
            bm.verts[i].co = mwi @ Vector(p.tolist()); moved.append(round(float(r[i] - 0.9 * med) * 1000, 1))
    rep[tok] = {'moved': len(moved), 'max_mm': max(moved) if moved else 0}
bm.to_mesh(me); me.update()
print('STUB_OUTLIERS', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
