"""HOF2 wrists, r2 (coordinator 2026-11-02: the grafted right-hand flap rose over the cuff in Running/Death; the earlier
trims, v9-v20, opened the back of the wrist instead). Weights only, from the untrimmed master (v8): every hand-graft
vertex (all its faces `hand`) behind the hand joint takes the weights of the nearest sleeve vertex (body faces of that arm,
before the joint), blended by smoothstep from its own at S_OWN to the sleeve's at S_FULL (s along forearm -> hand from the
hand joint), so the stub and the cuff around it move together and the bend happens at the joint, outside the cuff.
With RIGID=1 the target is the forearm joint alone, and the sleeve's own cuff (body vertices of that arm from CUFF_FROM
to the joint) blends to it too (smoothstep CUFF_FROM -> CUFF_FULL): v8's cuff carried 26 % of the hand, and the stub with
the same weights still rose 27 mm over it in Running (linear blending of the bent wrist), so cuff and stub are made one
rigid forearm piece and the wrist bends past the joint on bare skin.
Positions, faces and UVs unchanged. Args: <in blend> <out blend> [s_own 0.004] [s_full -0.008]"""
import os
RIGID = os.environ.get('RIGID') == '1'
CUFF_FROM, CUFF_FULL = float(os.environ.get('CUFF_FROM', '-0.09')), float(os.environ.get('CUFF_FULL', '-0.05'))
import bpy, bmesh, sys, json
import numpy as np
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
S_OWN = float(a[2]) if len(a) > 2 else 0.004
S_FULL = float(a[3]) if len(a) > 3 else -0.008
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['hand'], bm.faces.layers.int['head']
dl = bm.verts.layers.deform.verify()
gname = {g.index: g.name for g in ob.vertex_groups}
def sst(x, e0, e1):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0); return t * t * (3 - 2 * t)
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    ax = (a1 - a0) / np.linalg.norm(a1 - a0)
    def sr(p):
        rel = np.array(p) - a1; s = rel @ ax; return s, np.linalg.norm(rel - s * ax)
    arm = {i for i, n in gname.items() if f' {tok} ' in n and any(k in n for k in ('Forearm', 'Hand', 'UpperArm', 'Finger'))}
    sleeve = []
    for v in bm.verts:
        if not v.link_faces or any(f[lh] or f[lk] for f in v.link_faces): continue
        s, r = sr(mw @ v.co)
        if -0.15 < s < 0.0 and r < 0.09 and sum(w for g, w in v[dl].items() if g in arm) > 0.5:
            sleeve.append(v)
    fid = next(i for i, n in gname.items() if n == f'Bip01 {tok} Forearm')
    nc = 0
    if RIGID:
        for v in sleeve:
            sv = sr(mw @ v.co)[0]
            if sv <= CUFF_FROM: continue
            t = sst(sv, CUFF_FROM, CUFF_FULL); own = dict(v[dl].items())
            new = {g: (1 - t) * own.get(g, 0) + (t if g == fid else 0) for g in set(own) | {fid}}
            tot = sum(new.values())
            for g in list(v[dl].keys()): del v[dl][g]
            for g, w in new.items():
                if w / tot > 1e-4: v[dl][g] = w / tot
            nc += 1
    kd = KDTree(len(sleeve))
    for i, v in enumerate(sleeve): kd.insert(mw @ v.co, i)
    kd.balance()
    n = 0; smin = 9
    for v in bm.verts:
        if not v.link_faces or not all(f[lh] for f in v.link_faces): continue
        s, r = sr(mw @ v.co)
        if s >= S_OWN or r > 0.09 or s < -0.2: continue
        t = 1.0 - sst(s, S_FULL, S_OWN)
        _, i, _ = kd.find(mw @ v.co); tgt = {fid: 1.0} if RIGID else dict(sleeve[i][dl].items())
        own = dict(v[dl].items())
        new = {g: (1 - t) * own.get(g, 0) + t * tgt.get(g, 0) for g in set(own) | set(tgt)}
        tot = sum(new.values())
        for g in list(v[dl].keys()): del v[dl][g]
        for g, w in new.items():
            if w / tot > 1e-4: v[dl][g] = w / tot
        n += 1; smin = min(smin, s)
    rep[tok] = {'sleeve_verts': len(sleeve), 'stub_verts': n, 'deepest_s': round(float(smin), 3), 'cuff_verts': nc}
bm.to_mesh(ob.data); ob.data.update()
print('WRIST_WEIGHTS', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
