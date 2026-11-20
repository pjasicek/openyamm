"""Weight the fitted mouse 'Body' to the MM9 MOUSE.abc skeleton plus four small leg chains of our own.

Args: <fit blend> <out blend> <report json>

MM9's mouse has no legs (a 54-triangle body on six joints: Bone05 body, Bone08 neck, Bone06 snout, Bone01-03 tail),
so each paw gets one bone of ours under Bone05 (wrist/heel -> toe tips), placed per frame so planted paws stay
fixed on the floor; the short stub between paw and belly blends paw -> body and stretches with it.
Weights reproduce MM9's own rigid skin, made smooth (MM9 interpolates along its polygon edges between labelled rings):
- body along its length: Bone05 behind y -0.045, blending to Bone08 by y -0.062 (MM9's neck ring at -0.064; the
  chest under the head where the forelegs root stays on Bone05),
  Bone08 to y -0.088 (Bone06 pivot), blending to Bone06 by -0.100 (MM9's snout ring at -0.094); ears and skull follow
  Bone08, the muzzle Bone06;
- tail: arc distance u along the tube (negative into the rump): Bone05 -> Bone01 over u -6..+6 mm, then MM9's linear
  interpolation Bone01 (at Bone02's pivot) -> Bone02 (at Bone03's pivot) -> Bone03 (tip);
- legs: geodesic distance from each paw's toe tips: the paw bone up to 2 mm past the wrist/heel, fading into the
  body over the next 2.5 mm (only paws and their short stubs show below the body);
- eyes take their socket's weights (nearest head vertex).
"""
import bpy, bmesh, sys, json, heapq, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv

# leg joints in the bind pose, the creature's left (+X); the right side mirrors x. From the bottom/side renders of the
# fitted Meshy mouse (work/fit_v1.blend): front paw wrist -> toe tips, hind heel -> toe tips.
LEGS = {
    'F': {'top': (0.0115, -0.0560, 0.0140), 'mid': (0.0140, -0.0545, 0.0065), 'wrist': (0.0160, -0.0683, 0.0022),
          'toe': (0.0160, -0.0817, 0.0010)},
    'H': {'top': (0.0130, 0.0060, 0.0140), 'mid': (0.0170, -0.0040, 0.0080), 'wrist': (0.0131, 0.0107, 0.0025),
          'toe': (0.0225, -0.0057, 0.0010)},
}
LOW_BAND, FADE = 0.002, 0.0025
CAPSULE = {'F': 0.0040, 'H': 0.0042}   # paw region radius around the wrist/heel -> toe line

bpy.ops.wm.open_mainfile(filepath=FIT)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name != 'Body':
        bpy.data.objects.remove(o)

# ---------------- leg bones
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
leg_bones = {}
for leg, J in LEGS.items():
    for side, sx in (('L', 1), ('R', -1)):
        P = {k: Vector((v[0] * sx, v[1], v[2])) for k, v in J.items()}
        bone = eb.new(f'Leg{leg}{side}')
        bone.head, bone.tail = P['wrist'], P['toe']
        bone.roll = 0.0
        bone.parent = eb['Bone05']
        bone.use_connect = False
        leg_bones[leg + side] = bone.name
bpy.ops.object.mode_set(mode='OBJECT')
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}

me = body.data
n = len(me.vertices)
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
part = np.array([d.value for d in me.attributes['part'].data])
tail_t = np.array([d.value for d in me.attributes['tail_t'].data])
W = np.zeros((n, len(bones)))


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------- body along its length (Bone05 / Bone08 / Bone06)
y = P[:, 1]
# the chest under the head (where the forelegs root) stays on the body: the head swings without dragging the leg roots
chest = smooth(0.011, 0.005, P[:, 2]) * smooth(-0.092, -0.082, y)
w08 = smooth(-0.045, -0.062, y) * (1 - chest)
w06 = smooth(-0.088, -0.100, y)
W[:, bidx['Bone05']] = 1 - w08
W[:, bidx['Bone08']] = w08 * (1 - w06)
W[:, bidx['Bone06']] = w08 * w06

# ---------------- tail: arc distance along the tube
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
tail_ids = np.nonzero(tail_t >= 0)[0]
ring_t = np.unique(np.round(tail_t[tail_ids], 6))
centres = np.array([P[tail_ids[np.abs(tail_t[tail_ids] - t) < 1e-6]].mean(0) for t in ring_t])
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(centres, axis=0), axis=1))])


def arc_at(p):
    return float(arc[np.argmin(np.linalg.norm(centres - np.array(p), axis=1))])


u = np.full(n, -1.0)
for i in tail_ids:
    u[i] = float(np.interp(tail_t[i], ring_t, arc))
c0 = centres[0]
near = (tail_t < 0) & (piece == 0) & (P[:, 1] > c0[1] - 0.012)
u[near] = P[near, 1] - c0[1]
d2, d3, dt = arc_at(J['Bone02']), arc_at(J['Bone03']), float(arc[-1])
tail_like = (tail_t >= 0) | near
w01 = smooth(-0.006, 0.006, u)
seg = np.zeros((n, 4))   # Bone01, Bone02, Bone03 shares along the tail
a = np.clip((u - d2) / (d3 - d2), 0, 1)
b = np.clip((u - d3) / (dt - d3), 0, 1)
seg[:, 0] = np.where(u < d3, 1 - a, 0)
seg[:, 1] = np.where(u < d3, a, 1 - b)
seg[:, 2] = np.where(u < d3, 0, b)
for i in np.nonzero(tail_like)[0]:
    W[i] = 0
    W[i, bidx['Bone05']] = 1 - w01[i]
    W[i, bidx['Bone01']] = w01[i] * seg[i, 0]
    W[i, bidx['Bone02']] = w01[i] * seg[i, 1]
    W[i, bidx['Bone03']] = w01[i] * seg[i, 2]
report = {'tail': {'arc_bone02': d2, 'arc_bone03': d3, 'length': dt, 'rump_verts': int(near.sum())}}

# ---------------- legs: geodesic distance from the toe tips
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nbr = [[(e.other_vert(v).index, e.calc_length()) for e in v.link_edges] for v in bm.verts]


def geodesic(seeds, limit):
    dist = np.full(n, np.inf)
    h = []
    for s in seeds:
        dist[s] = 0.0
        heapq.heappush(h, (0.0, s))
    while h:
        d, i = heapq.heappop(h)
        if d > dist[i] or d > limit:
            continue
        for j, l in nbr[i]:
            nd = d + l
            if nd < dist[j]:
                dist[j] = nd
                heapq.heappush(h, (nd, j))
    return dist


report['legs'] = {}
body_mask = (piece == 0) & (tail_t < 0)
for leg, Jl in LEGS.items():
    for side, sx in (('L', 1), ('R', -1)):
        toe = np.array([Jl['toe'][0] * sx, Jl['toe'][1], Jl['toe'][2]])
        wrist = np.array([Jl['wrist'][0] * sx, Jl['wrist'][1], Jl['wrist'][2]])
        paw_len = float(np.linalg.norm(toe - wrist))
        cand = np.nonzero(body_mask & (P[:, 2] < 0.0035) & (np.linalg.norm(P - toe, axis=1) < 0.0035))[0]
        g = geodesic(list(cand), paw_len + LOW_BAND + FADE + 0.002)
        name = leg_bones[leg + side]
        w_leg = 1 - smooth(paw_len + LOW_BAND, paw_len + LOW_BAND + FADE, g)
        # only the paw and its stub: near the wrist-toe line and below the belly (the hind foot lies against it)
        ax = toe - wrist
        tt = np.clip(((P - wrist) @ ax) / (ax @ ax), -0.25, 1.0)
        dline = np.linalg.norm(P - (wrist + tt[:, None] * ax), axis=1)
        w_leg = w_leg * (1 - smooth(CAPSULE[leg] - 0.0012, CAPSULE[leg], dline)) * (1 - smooth(0.0045, 0.0065, P[:, 2]))
        sel = np.nonzero(body_mask & (w_leg > 0))[0]
        for i in sel:
            keep = W[i] * (1 - w_leg[i])
            W[i] = keep
            W[i, bidx[name]] += w_leg[i]
        report['legs'][leg + side] = {'seeds': len(cand), 'verts': len(sel), 'paw_len': paw_len,
                                      'full_paw': int((w_leg > 0.99).sum())}

# ---------------- eyes: the socket's weights
eye_ids = np.nonzero(piece == 1)[0]
head_ids = np.nonzero((piece == 0) & (P[:, 1] < -0.08))[0]
kd = KDTree(len(head_ids))
for j, i in enumerate(head_ids):
    kd.insert(Vector(P[i]), j)
kd.balance()
for side in (1, -1):
    ids = eye_ids[np.sign(P[eye_ids, 0]) == side]
    c = P[ids].mean(0)
    W[ids] = W[head_ids[kd.find(Vector(c))[1]]]

# ---------------- write: four influences, normalised
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]
    row = np.zeros(len(bones)); row[keep] = W[i, keep]
    row[row < 0.01] = 0
    W[i] = row / row.sum()
for b in bones:
    body.vertex_groups.new(name=b)
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[bones[j]].add([i], float(W[i, j]), 'REPLACE')
for gr in list(body.vertex_groups):
    if not np.any(W[:, bidx[gr.name]] > 0):
        body.vertex_groups.remove(gr)
body.parent = arm
body.matrix_parent_inverse = arm.matrix_world.inverted()
mod = body.modifiers.new('Armature', 'ARMATURE'); mod.object = arm
col = me.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
rng = np.random.default_rng(7)
pal = rng.uniform(0.15, 1.0, (len(bones), 3))
for i in range(n):
    col.data[i].color = (*(W[i, :, None] * pal).sum(0), 1.0)
report['dominant_counts'] = {bones[j]: int((W[:, j] > 0.5).sum()) for j in range(len(bones)) if (W[:, j] > 0).any()}
report['unweighted'] = int((W.sum(1) == 0).sum())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('RIG ' + json.dumps(report))
