"""Finger joints and weights on a (reduced) rigged Body, by connectivity. Args: <in blend> <out blend> <config json>
Digits come from digits.py; every finger keeps `digit_len` from its tip so the knuckles sit level across the palm, and the
fingers' first joints are the knuckles. Bones are translated only. Weights: hand > three phalanges by the position along
the chain, palm on the hand."""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digits as DG
IN, OUT, CFG = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
P = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    nbr[a].append(b); nbr[b].append(a)
cur = {b.name: np.array(tuple(rig.matrix_world @ b.head_local)) for b in rig.data.bones}
J = {k: np.array(v) for k, v in json.load(open(cfg['mm9_joints'])).items()}
dg = DG.find_digits(P, nbr, cfg['digits'], cur, J)
print('DONE digits', json.dumps(dg['report'])[:900])
new = dict(cur); new.update(dg['joints'])
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = rig.matrix_world.inverted()
for eb in rig.data.edit_bones:
    if eb.name in dg['joints']:
        d = Mi.to_3x3() @ Vector(new[eb.name] - cur[eb.name])
        eb.head += d; eb.tail += d
bpy.ops.object.mode_set(mode='OBJECT')


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def poly_param(Q, pts):
    best = np.full(len(Q), 1e9); s = np.zeros(len(Q)); L0 = 0.0
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        ab = b - a; L = np.linalg.norm(ab)
        t = (Q - a) @ ab / (L * L)
        tc = np.clip(t, None if i == 0 else 0, None if i == len(pts) - 2 else 1)
        d = np.linalg.norm(Q - a - np.outer(tc, ab), axis=1)
        m = d < best
        best[m] = d[m]; s[m] = L0 + tc[m] * L
        L0 += L
    return s, best


B = cfg['finger_blend']
for S in ('L', 'R'):
    # every hand-family vertex goes to Hand first
    fam = [b.name for b in rig.data.bones if f' {S} Finger' in b.name]
    hd = f'Bip01 {S} Hand'
    hg = body.vertex_groups[hd]
    for v in me.vertices:
        tot = 0
        for g in list(v.groups):
            nm = body.vertex_groups[g.group].name
            if nm in fam:
                tot += g.weight
                body.vertex_groups[g.group].remove([v.index])
        if tot > 0:
            hg.add([v.index], tot, 'ADD')
for key, ids in dg['labels'].items():
    ch = key.split('|')
    if 'Finger' not in ch[0]:
        continue
    S = ch[0].split()[1]
    tipv = ids[np.argmax(np.linalg.norm(P[ids] - new[ch[0]], axis=1))]
    pts = [new[c] for c in ch] + [P[tipv]]
    s, d = poly_param(P[ids], pts)
    L = np.cumsum([np.linalg.norm(b - a) for a, b in zip(pts[:-1], pts[1:])])
    w1 = sstep(s, -B, B); w2 = sstep(s, L[0] - B, L[0] + B); w3 = sstep(s, L[1] - B, L[1] + B)
    W4 = np.stack([1 - w1, w1 * (1 - w2), w2 * (1 - w3), w3], 1)
    hd = f'Bip01 {S} Hand'
    for gname in ch:
        if gname not in body.vertex_groups:
            body.vertex_groups.new(name=gname)
    groups = [body.vertex_groups[hd]] + [body.vertex_groups[c] for c in ch]
    for i, vid in enumerate(ids):
        vid = int(vid)
        for g in list(me.vertices[vid].groups):
            body.vertex_groups[g.group].remove([vid])
        for gg, w in zip(groups, W4[i]):
            if w > 0.01:
                gg.add([vid], float(w), 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('DONE fingers', OUT)
