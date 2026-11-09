"""Body cuff remnant follows the grafted hand (2026-11-02, sleeve_poke_gate + wrist close-ups): graft_hands.py cut the
old hand away along the hand-weight border, so body faces reach 0-5 cm past the hand joint in a toothed rim over the
MPFB hand. Those body vertices kept forearm-heavy weights, so a bent wrist left the teeth behind as shards standing off
the hand (Dump, RubBeard, Fidget, Death). Per side, rest pose: body (non-hand-face) vertices within RAD of the
forearm -> hand axis and s (along it, from the hand joint) > S0 take the weights of the nearest grafted-hand vertex,
blended in by smoothstep over S0..S1 (fully the hand's past S1), so the rim moves with the hand it lies on.
Weights only (geometry, UVs and attributes unchanged). Args: -- <in blend> <out blend>"""
import bpy, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
S0, S1, RAD = -0.03, 0.0, 0.08
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world
nv = len(me.vertices)
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
hand_attr = np.zeros(len(me.polygons), np.int32)
me.attributes['hand'].data.foreach_get('value', hand_attr)
gname = {g.index: g.name for g in body.vertex_groups}
BONES = {b.name for b in rig.data.bones}
W = [{gname[g.group]: g.weight for g in v.groups if g.weight > 0 and gname[g.group] in BONES} for v in me.vertices]
handv = np.zeros(nv, bool)
bodyv = np.zeros(nv, bool)
for p in me.polygons:
    (handv if hand_attr[p.index] else bodyv)[list(p.vertices)] = True
onlybody = bodyv & ~handv
rep = {}
for tok in ('L', 'R'):
    a0 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Forearm'].head_local)
    a1 = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {tok} Hand'].head_local)
    axis = (a1 - a0) / np.linalg.norm(a1 - a0)
    s = (CO - a1) @ axis
    rad = np.linalg.norm(CO - a1 - np.outer(s, axis), axis=1)
    side = np.sign(CO[:, 0]) == np.sign(a1[0])
    hv = np.nonzero(handv & side & (rad < RAD) & (s > S0 - 0.03))[0]
    tree = KDTree(len(hv))
    for n_, i in enumerate(hv):
        tree.insert(Vector(CO[i]), n_)
    tree.balance()
    sel = np.nonzero(onlybody & side & (rad < RAD) & (s > S0))[0]
    for i in sel:
        k = float(np.clip((s[i] - S0) / (S1 - S0), 0, 1)); k = k * k * (3 - 2 * k)
        _, j, _ = tree.find(Vector(CO[i]))
        src = W[hv[j]]
        mix = {}
        for g, w in W[i].items():
            mix[g] = mix.get(g, 0) + (1 - k) * w
        for g, w in src.items():
            mix[g] = mix.get(g, 0) + k * w
        top = sorted(mix.items(), key=lambda x: -x[1])[:4]
        t = sum(w for _, w in top)
        W[i] = {g: w / t for g, w in top}
    rep[tok] = {'body_verts': int(len(sel)), 'hand_verts': int(len(hv)), 's_max': round(float(s[sel].max()), 3) if len(sel) else None}
for g in body.vertex_groups:
    if g.name in BONES:
        g.remove(list(range(nv)))
groups = {g.name: g for g in body.vertex_groups}
for i, w in enumerate(W):
    for gn, wt in w.items():
        if gn not in groups:
            groups[gn] = body.vertex_groups.new(name=gn)
        groups[gn].add([i], wt, 'REPLACE')
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CUFF_FOLLOW', json.dumps(rep))
