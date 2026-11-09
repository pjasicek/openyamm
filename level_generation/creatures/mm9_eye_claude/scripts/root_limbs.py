"""Root the Eye's legs in the body and pin the stalk tips to their eyeballs (2026-10-30 fix; runs on the UV blend, so
UVs, textures and the retexture stay valid).

Args: <uv blend> <out blend> <report json>

Why: fit_eye.py maps every Meshy leg piece onto its MM9 chain from the chain's root joint, and the MM9 leg root joints
(Box37, Box29, Box28, Box15, Box33, Box42, Box48, Box52) lie 1.6-12 cm below our HD body shell, so the legs started in
the air. Stalks end at their eyeball bone's head while each eyeball is centred on MM9's eyeball vertices: the Box06
eyeball sat 14.3 cm from the Box03 stalk's tip (3.6 cm gap), and stalk tips carried little or no eyeball-bone weight.

Legs: the root bone's axis (J0 -> J1) cast back from J0 hits the body after h; the leg's first segment (from its root
cap to J1) is stretched along that axis so the cap ends DEPTH (max 3 cm, 3 rod radii) inside the shell. J1 and the
rest of the leg stay where they are; vertices move only along the axis (the rod keeps its section, its UVs and
texture). Weights of the extension (in front of J0) blend from the leg's own to the body's weights at the hit point
(barycentric), fully the body's from just inside the shell, so the buried root follows the body surface it enters.
Stalks: an eyeball whose stalk tip ends outside it moves rigidly onto the tip (STALK_IN inside); stalk vertices within
REACH of their eyeball's surface blend to the eyeball bone (fully inside it), so MM9's turn of the small eye carries
the stalk tip with it.
"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_cfg as E

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
DEPTH_MIN = 0.03
REACH = 0.035
STALK_IN = 0.03
ROOTED = 0.005


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


bpy.ops.wm.open_mainfile(filepath=IN)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
n = len(me.vertices)
piece = np.array([d.value for d in me.attributes['piece'].data])
chain = np.array([d.value for d in me.attributes['chain'].data])
M = body.matrix_world
Mi = M.inverted()
co = [M @ v.co for v in me.vertices]
groups = [g.name for g in body.vertex_groups]
gidx = {g: i for i, g in enumerate(groups)}


def ensure_group(name):
    if name not in gidx:
        body.vertex_groups.new(name=name)
        groups.append(name)
        gidx[name] = len(groups) - 1
    return gidx[name]


for c in E.STALKS:
    ensure_group(c[-1])
W = np.zeros((n, len(groups)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
core = (chain == -1) & (piece == 0)
polys = [p.vertices[:] for p in me.polygons if all(core[i] for i in p.vertices)]
bvh = BVHTree.FromPolygons(co, polys)
J = {b.name: arm.matrix_world @ b.head_local for b in arm.data.bones}
report = {'legs': {}, 'stalks': {}}
newco = list(co)
newW = W.copy()

for k, ch in enumerate(E.LEGS):
    j0, j1 = J[ch[0]], J[ch[1]]
    L1 = (j1 - j0).length
    a = (j1 - j0) / L1
    loc, nrm, fi, h = bvh.ray_cast(j0, -a, 1.0)
    assert loc is not None, ch[0]
    ids = np.nonzero((chain == k) & (piece == 0))[0]
    s = np.array([(co[i] - j0).dot(a) for i in ids])
    r = np.array([((co[i] - j0) - a * si).length for si, i in zip(s, ids)])
    first = (s < L1) & (r < 0.06)
    s_min = float(s[first].min())
    radius = float(np.median(r[first & (s > 0) & (s < 0.12)]))
    depth = max(DEPTH_MIN, 3 * radius)
    s0 = -(h + depth)
    stretch = (L1 - s0) / (L1 - s_min)
    # body weights at the hit point (barycentric on the hit triangle)
    tri = polys[fi]
    A, B, C = (co[i] for i in tri)
    v0, v1, v2 = B - A, C - A, loc - A
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    bv = (d11 * d20 - d01 * d21) / den
    bw = (d00 * d21 - d01 * d20) / den
    bary = (1 - bv - bw, bv, bw)
    Wb = sum(bary[m] * W[tri[m]] for m in range(3))
    moved = 0
    for si, i, f in zip(s, ids, first):
        if not f:
            continue
        sn = s0 + (si - s_min) * stretch
        newco[i] = co[i] + a * (sn - si)
        moved += 1
        if sn < 0:
            t = smooth(-sn / (h + 0.5 * depth))
            newW[i] = (1 - t) * W[i] + t * Wb
    report['legs'][ch[0]] = {'gap_along_axis': round(h, 4), 'depth': round(depth, 4), 'rod_radius': round(radius, 4),
                            'first_segment': round(L1, 4), 'stretch': round(stretch, 3), 'moved': moved,
                            'body_weights': {groups[g]: round(float(Wb[g]), 3) for g in np.nonzero(Wb > 0.01)[0]}}

for k0, ch in enumerate(E.STALKS):
    k = len(E.LEGS) + k0
    eb = gidx[ch[-1]]
    ball = np.nonzero((chain == k) & (piece == 2))[0]
    ball_set = set(ball.tolist())
    ids = np.nonzero((chain == k) & (piece == 0))[0]
    cen = sum((co[i] for i in ball), Vector()) / len(ball)
    R = float(np.mean([(co[i] - cen).length for i in ball]))
    # the stalk ends at its eyeball bone's head; an eyeball the stalk does not enter (by ROOTED; Box06: 3.6 cm gap, its
    # centre 14.3 cm from the tip, beside it) moves rigidly (no rotation) towards the tip, along the mean of the stalk
    # axis and its old direction, until the open tip is STALK_IN inside it
    base, end = J[ch[-2]], J[ch[-1]]
    a = (end - base).normalized()
    bvh0 = BVHTree.FromPolygons(co, [p.vertices[:] for p in me.polygons if all(i in ball_set for i in p.vertices)])
    depth = 0.0
    for i in ids:
        loc, nrm, _, d = bvh0.find_nearest(co[i])
        if (co[i] - loc).dot(nrm) < 0:
            depth = max(depth, d)
    moved = 0.0
    if depth < ROOTED:
        u = (a + (cen - end).normalized()).normalized()
        shift = end + u * (R - STALK_IN) - cen
        for i in ball:
            newco[i] = co[i] + shift
        moved = shift.length
    ball_bvh = BVHTree.FromPolygons(newco, [p.vertices[:] for p in me.polygons
                                            if all(i in ball_set for i in p.vertices)])
    blended = 0
    for i in ids:
        loc, nrm, _, d = ball_bvh.find_nearest(newco[i])
        inside = (newco[i] - loc).dot(nrm) < 0
        t = 1.0 if inside else smooth((REACH - d) / REACH)
        if t > 0:
            row = newW[i] * (1 - t)
            row[eb] += t
            newW[i] = row
            blended += 1
    report['stalks'][ch[0]] = {'eyeball_bone': ch[-1], 'eyeball_radius': round(R, 4),
                               'tip_to_centre_before': round((cen - end).length, 4),
                               'stalk_depth_in_ball_before': round(depth, 4), 'eyeball_moved': round(moved, 4),
                               'blended': blended}

# at most four influences, normalised
for i in range(n):
    row = newW[i]
    keep = np.argsort(-row)[:4]
    out = np.zeros_like(row)
    out[keep] = row[keep]
    out[out < 0.02] = 0
    newW[i] = out / out.sum()
for i, p in enumerate(newco):
    me.vertices[i].co = Mi @ p
for g in body.vertex_groups:
    g.remove(list(range(n)))
for i in range(n):
    for j in np.nonzero(newW[i])[0]:
        body.vertex_groups[groups[j]].add([i], float(newW[i, j]), 'REPLACE')
me.update()
report['changed_weights'] = int((np.abs(newW - W) > 1e-4).any(1).sum())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('ROOTS ' + json.dumps({k: (v['gap_along_axis'], v['stretch']) for k, v in report['legs'].items()}))
print('STALKS ' + json.dumps(report['stalks']))
