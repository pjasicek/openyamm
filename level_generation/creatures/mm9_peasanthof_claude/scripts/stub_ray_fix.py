"""Hand-material vertices outside the sleeve (sleeve_poke_gate's own test at rest, then fixed): per side, every vertex of a
hand face within -0.15..+0.03 m of the hand joint along forearm -> hand casts a ray from the forearm axis, perpendicular to
it, through itself against the arm's body faces (non-head, non-hand, mostly weighted to that side's UpperArm/Forearm/Hand);
if the vertex lies beyond the hit by more than TOL it moves in to 0.9 x the hit radius and takes the weights of the
nearest sleeve vertex. Positions and weights only. Args: <in blend> <out blend> [tol 0.002]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
TOL = float(a[2]) if len(a) > 2 else 0.002
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = ob.data; mw = ob.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
dl = bm.verts.layers.deform.verify()
gnames = {g.index: g.name for g in ob.vertex_groups}
rep = {}
for tok in ('L', 'R'):
    gid = {g.index for g in ob.vertex_groups if g.name in (f'Bip01 {tok} UpperArm', f'Bip01 {tok} Forearm', f'Bip01 {tok} Hand')}
    def arm_w(v): return sum(w for g, w in v[dl].items() if g in gid)
    sleeve = [f for f in bm.faces if f[lh] == 0 and f[lk] == 0 and sum(arm_w(v) for v in f.verts) / len(f.verts) > 0.5]
    vs = sorted({v for f in sleeve for v in f.verts}, key=lambda v: v.index); idx = {v.index: i for i, v in enumerate(vs)}
    bvh = BVHTree.FromPolygons([mw @ v.co for v in vs], [[idx[v.index] for v in f.verts] for f in sleeve])
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    cand = {v for f in bm.faces if f[lh] != 0 or f[lk] != 0 for v in f.verts}
    moved = []
    for v in cand:
        p = np.array(tuple(mw @ v.co)); s = (p - a1) @ ax
        if not (-0.15 < s < 0.03): continue
        foot = a1 + s * ax; d = p - foot; r = np.linalg.norm(d)
        if r < 1e-6 or r > 0.12: continue
        hit = bvh.ray_cast(Vector(foot.tolist()), Vector((d / r).tolist()), 0.12)
        if hit[0] is None: continue
        rh = (np.array(hit[0][:]) - foot) @ (d / r)
        if r - rh > TOL:
            v.co = mwi @ Vector((foot + d / r * 0.9 * rh).tolist())
            near = min(vs, key=lambda q: (q.co - v.co).length)
            for g in list(v[dl].keys()): del v[dl][g]
            for g, w in near[dl].items(): v[dl][g] = w
            moved.append(round(float(r - rh) * 1000, 1))
    # REWEIGHT_S: stub vertices further up the forearm than this (m, negative) blend toward the nearest sleeve vertex's
    # weights (REWEIGHT_K), so the stub moves with the cuff in bent wrists (Running/Death poked 25-27 mm)
    import os
    RS = os.environ.get('REWEIGHT_S'); RK = float(os.environ.get('REWEIGHT_K', '0.8')); nre = 0
    if RS:
        for v in cand:
            p = np.array(tuple(mw @ v.co)); sv = (p - a1) @ ax
            if not (-0.15 < sv < float(RS)): continue
            if np.linalg.norm(p - (a1 + sv * ax)) > 0.12: continue
            near = min(vs, key=lambda q: (q.co - v.co).length)
            old = dict(v[dl].items()); new = {g: w * RK for g, w in near[dl].items()}
            for g, w in old.items(): new[g] = new.get(g, 0.0) + w * (1 - RK)
            for g in list(v[dl].keys()): del v[dl][g]
            for g, w in new.items(): v[dl][g] = w
            nre += 1
    rep[tok] = {'moved': len(moved), 'max_mm': max(moved) if moved else 0, 'reweighted': nre}
bm.to_mesh(me); me.update()
print('STUB_RAY_FIX', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
