"""Tuck the grafted hands' forearm stub inside the sleeves (user review 2026-11-01, Bjarni: "hands sticking through the
sleeves"). graft_hands.py conformed the MPFB stub to the cuff OPENING; above the cuff the Meshy sleeve narrows and the stub
pokes out on the inner/back side of the sleeve (up to 14.5 mm at rest, sleeve_poke_gate.py).

Per side, rest pose: axis = forearm joint -> hand joint. Every hand-face vertex (face attribute `hand` = 1) up to SPAN past
the hand joint casts a ray from the axis, perpendicular to it, through itself against that arm's sleeve (non-hand faces
whose vertices are mostly weighted to the side's UpperArm/Forearm/Hand); where it hits within REACH and the vertex is
further out than FRAC x the hit distance minus GAP, it moves in to that radius. A vertex whose ray finds no sleeve (the
visible hand past the cuff) stays. Then, with WEIGHTS, vertices more than DEEP up the sleeve from the hand joint take the
weights of the nearest sleeve vertex (blend over BLEND m), so the stub moves with the cloth it hides under in every clip.
Geometry and weights only: UVs (HeadUV/UVMap), attributes and face counts are unchanged, so the paid textures stay valid.
Args: -- <in blend> <out blend> [frac 0.82] [gap 0.002] [weights 1]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
FRAC = float(a[2]) if len(a) > 2 else 0.82
GAP = float(a[3]) if len(a) > 3 else 0.002
WEIGHTS = (a[4] if len(a) > 4 else '1') == '1'
SPAN, REACH, DEEP, BLEND = 0.03, 0.10, 0.010, 0.02
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world; mwi = mw.inverted()
nv = len(me.vertices)
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
hand_attr = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand_attr)
gname = {g.index: g.name for g in body.vertex_groups}
BONES = {b.name for b in rig.data.bones}
# deform weights only (graft_hands.py also keeps MPFB's own weights in MP_* groups, which are left as they are)
W = [{gname[g.group]: g.weight for g in v.groups if g.weight > 0 and gname[g.group] in BONES} for v in me.vertices]
dom = [max(w, key=w.get) if w else '' for w in W]
rep = {}
moved_total = 0
for tok in ('L', 'R'):
    arm = {f'Bip01 {tok} {k}' for k in ('UpperArm', 'Forearm', 'Hand')}
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    L = np.linalg.norm(a1 - a0); axis = (a1 - a0) / L
    onarm = np.array([d in arm for d in dom])
    sleeve_faces = [p for p in me.polygons if not hand_attr[p.index] and onarm[list(p.vertices)].sum() >= 2]
    sv = sorted({i for p in sleeve_faces for i in p.vertices})
    verts = [Vector(CO[i]) for i in range(nv)]
    bvh = BVHTree.FromPolygons(verts, [list(p.vertices) for p in sleeve_faces])
    hv = sorted({i for p in me.polygons if hand_attr[p.index] for i in p.vertices})
    hv = [i for i in hv if (CO[i] - a0) @ axis < L + SPAN and np.linalg.norm(np.cross(CO[i] - a0, axis)) < 0.12]
    moved, maxin = 0, 0.0
    for i in hv:
        t = (CO[i] - a0) @ axis
        p0 = a0 + t * axis
        r = CO[i] - p0; rv = np.linalg.norm(r)
        if rv < 1e-5:
            continue
        rd = r / rv
        # the OUTERMOST sleeve wall along the ray: the old forearm skin left under the sleeve (Meshy closed the sleeve
        # onto it) is hit first, 1-2 mm from the axis, and hid the outer wall in the first version
        rs, start = None, Vector(p0)
        for _ in range(8):
            hit = bvh.ray_cast(start, Vector(rd), REACH)
            if hit[0] is None:
                break
            rs = (np.array(hit[0]) - p0) @ rd
            start = hit[0] + Vector(rd) * 1e-4
            if rs > REACH:
                break
        if rs is None:
            continue
        target = FRAC * rs - GAP
        if rv > target and target > 0.004:
            CO[i] = p0 + rd * target; moved += 1; maxin = max(maxin, rv - target)
    rep[tok] = {'hand_verts': len(hv), 'moved': moved, 'max_in_mm': round(maxin * 1000, 1), 'sleeve_faces': len(sleeve_faces)}
    moved_total += moved
    if WEIGHTS:
        from mathutils.kdtree import KDTree
        tree = KDTree(len(sv))
        for n_, i_ in enumerate(sv):
            tree.insert(Vector(CO[i_]), n_)
        tree.balance()
        nw = 0
        for i in hv:
            t = (CO[i] - a0) @ axis
            depth = L - t                        # how far up the sleeve from the hand joint
            if depth <= DEEP:
                continue
            k = float(np.clip((depth - DEEP) / BLEND, 0, 1))
            _, j, _ = tree.find(Vector(CO[i]))
            src = W[sv[j]]
            mix = {}
            for g, w in W[i].items():
                mix[g] = mix.get(g, 0) + (1 - k) * w
            for g, w in src.items():
                mix[g] = mix.get(g, 0) + k * w
            top = sorted(mix.items(), key=lambda x: -x[1])[:4]
            s = sum(w for _, w in top)
            W[i] = {g: w / s for g, w in top}
            nw += 1
        rep[tok]['reweighted'] = nw
for i in range(nv):
    me.vertices[i].co = mwi @ Vector(CO[i])
if WEIGHTS:
    for g in body.vertex_groups:
        if g.name in BONES:
            g.remove(list(range(nv)))
    groups = {g.name: g for g in body.vertex_groups}
    for i, w in enumerate(W):
        for gname_, wt in w.items():
            groups[gname_].add([i], wt, 'REPLACE')
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SLEEVE_TUCK', json.dumps(rep))
