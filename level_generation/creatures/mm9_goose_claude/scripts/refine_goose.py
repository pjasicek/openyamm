"""Weight refinement of the rigged goose (after rig_body.py; same mesh).

Args: <rig blend> <out blend> <report json>

1. Webbed feet: nearest-MM9-vertex labels split the toes unevenly (MM9's toe bones carry 7-17 vertices and its left
   and right toe names are not mirrored). The web curls as one plate (see the comment in the loop).
2. Mirror: MM9's body is mirror-symmetric (the legs are staggered in its bind pose), so every non-leg vertex on the
   left (+X) copies the weights of its mirror vertex on the right. Body bones lie on the mid-plane: no renaming.
3. At most four influences, normalised.
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
TOE_SIGMA = math.radians(float(os.environ.get('TOE_SIGMA_DEG', '18')))
TOE_ALONG = (0.0, 0.03)
FEET = {'r': ('Xleg', 'Xfoot', ['Xtoea', 'Xtoeb', 'Xtoec']), 'l': ('Xleg01', 'Xfoot01', ['Xtoea01', 'Xtoeb01', 'Xtoec01'])}
bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
src = bpy.data.libraries  # noqa
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
n = len(me.vertices)
W = np.zeros((n, len(bones)))
gname = {g.index: g.name for g in body.vertex_groups}
for v in me.vertices:
    for g in v.groups:
        W[v.index, bidx[gname[g.group]]] = g.weight
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
# MM9 toe tips from the source mesh (dominant label), loaded from the fit's source blend
mm9 = bpy.data.objects.get('goose.mesh')
rep = {}
if mm9 is None:
    with bpy.data.libraries.load(os.environ['MM9_BLEND']) as (s_, d_):
        d_.objects = ['goose.mesh']
    mm9 = d_.objects[0]
mg = {g.index: g.name for g in mm9.vertex_groups}
MP = np.array([tuple(mm9.matrix_world @ v.co) for v in mm9.data.vertices])
ML = np.array([mg[max(v.groups, key=lambda g: g.weight).group] for v in mm9.data.vertices])
for k, (side, (leg, foot, toes)) in enumerate(FEET.items()):
    ank = J[foot]
    dirs = []
    for t in toes:
        tv = MP[ML == t]
        tip = tv[np.argmax(np.linalg.norm(tv - ank, axis=1))]
        d = (tip - ank)[:2]
        dirs.append(d / np.linalg.norm(d))
    dirs = np.array(dirs)
    # the web curls as one plate: MM9 curls the three toes of a foot together (16-89 deg, similar per foot), and
    # splitting a Meshy web between toes by angle tore it (the toes' directions are hard to find on a web with a
    # hind spur). Every web vertex in front of the ankle takes the three toes equally, ramped in along MM9's mean toe
    # direction from the ankle (TOE_ALONG), so the web never splits; the tarsus and the spur stay on Xfoot.
    fdir = np.mean(dirs, 0); fdir /= np.linalg.norm(fdir)
    sel = np.nonzero((chain == k) & (piece == 0) & (P[:, 2] < 0.045))[0]
    for i in sel:
        along = (P[i, :2] - ank[:2]) @ fdir
        x = np.clip((along - TOE_ALONG[0]) / (TOE_ALONG[1] - TOE_ALONG[0]), 0, 1)
        f = x * x * (3 - 2 * x)
        new = np.zeros(len(bones))
        new[bidx[foot]] = 1 - f
        for t in toes:
            new[bidx[t]] += f / len(toes)
        z = np.clip((P[i, 2] - 0.015) / 0.015, 0, 1)
        fw = np.clip((along - 0.01) / 0.015, 0, 1)
        g = 1 - (z * z * (3 - 2 * z)) * (1 - fw * fw * (3 - 2 * fw))   # toes and claws fully, the tarsus fades out
        W[i] = (1 - g) * W[i] + g * new
    rep[f'foot_{side}'] = {'verts': int(len(sel)), 'toes': toes, 'toe_dirs_deg': [round(math.degrees(math.atan2(d[1], d[0])), 1) for d in dirs]}
# neck: weights by the axial position along the MM9 joint polyline Xback -> XneckA -> XneckC -> XneckD -> XneckE ->
# Xhead (hat functions centred on each bone's segment, so a joint splits its two bones 50/50 and the neck bends as a
# smooth curve; nearest-vertex labels gave a kink mid-neck). The skull and bill are rigid on Xhead within HEAD_R of
# the mid-eye point (Xbeak never moves against Xhead in MM9's clips), fading into the neck weights by HEAD_FADE;
# the neck weights fade into the body's below NECK_Z.
CH = ['Xback', 'XneckA', 'XneckC', 'XneckD', 'XneckE', 'Xhead']
JP = np.array([J[b] for b in CH])
segs = list(zip(JP[:-1], JP[1:]))
eyes = np.nonzero(piece == 2)[0]
em = P[eyes].mean(0); em[0] = 0.0
HEAD_R = float(os.environ.get('HEAD_R', '0.045'))
HEAD_FADE = float(os.environ.get('HEAD_FADE', '0.03'))
NECK_Z = (0.40, 0.47)


def sst(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


nn = 0
for i in np.nonzero(piece == 0)[0]:
    if P[i, 2] < NECK_Z[0]:
        continue
    best = (9.0, 0.0)
    for k, (a, b) in enumerate(segs):
        ab = b - a
        u = float(np.clip((P[i] - a) @ ab / (ab @ ab), 0, 1))
        d = np.linalg.norm(P[i] - (a + u * ab))
        if d < best[0]:
            best = (d, k + u)
    s_ = best[1]                       # 0 = Xback joint ... 5 = Xhead joint
    new = np.zeros(len(bones))
    for k in range(len(CH)):
        c = k + 0.5
        w = max(0.0, 1 - abs(s_ - c))
        if k == len(CH) - 1:
            w = 1.0 if s_ >= c else w
        if k == 0:
            w = 1.0 if s_ <= c else w
        new[bidx[CH[k]]] += w
    new /= new.sum()
    hr = np.linalg.norm(P[i] - em)
    h = 1 - sst(HEAD_R, HEAD_R + HEAD_FADE, hr)
    if P[i, 1] < em[1]:
        h = max(h, 1 - sst(0.0, HEAD_FADE, P[i, 1] - em[1] + 0.0) if hr < 0.2 else h)   # the whole bill
    head = np.zeros(len(bones)); head[bidx['Xhead']] = 1
    new = (1 - h) * new + h * head
    a = sst(*NECK_Z, P[i, 2])
    W[i] = (1 - a) * W[i] + a * new
    nn += 1
rep['neck_axial_verts'] = nn
# eyes share their socket's weights (nearest body vertex)
bodyv = np.nonzero(piece == 0)[0]
kb = KDTree(len(bodyv))
for j, i in enumerate(bodyv):
    kb.insert(tuple(P[i]), j)
kb.balance()
for i in eyes:
    W[i] = W[bodyv[kb.find(tuple(P[i]))[1]]]
# mirror the non-leg body weights (+X copies -X)
leg_bones = [bidx[b] for f in FEET.values() for b in [f[0], f[1]] + f[2]]
legw = W[:, leg_bones].sum(1)
right = np.nonzero((P[:, 0] < -1e-5) & (piece == 0))[0]
kd = KDTree(len(right))
for j, i in enumerate(right):
    kd.insert((-P[i, 0], P[i, 1], P[i, 2]), j)
kd.balance()
mirrored, far = 0, 0
for i in np.nonzero((P[:, 0] > 1e-5) & (piece == 0))[0]:
    if legw[i] > 1e-3:
        continue
    co, j, d = kd.find(tuple(P[i]))
    m = right[j]
    if d > 2e-3 or legw[m] > 1e-3:
        far += 1
        continue
    W[i] = W[m]
    mirrored += 1
rep['mirrored'] = mirrored
rep['mirror_skipped'] = far
# eyes (piece 2) keep the weights of their socket vertex (rig_body); re-copy after the mirror
for i in np.nonzero(piece == 2)[0]:
    pass
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.02] = 0
    W[i] = row / row.sum()
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bidx[g.name]] > 0):
        body.vertex_groups.remove(g)
rep['dominant_counts'] = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('REFINE ' + json.dumps(rep))
