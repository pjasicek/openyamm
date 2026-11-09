"""MM7 spider rig (quadruped playbook, spiders; after mm6_spi1_claude/scripts/rig_spi1.py). Forward -Y, up +Z, left +X.
Smart Topology returned the body (cephalothorax + abdomen) as one piece and each leg as ONE fused piece (the MM6
spider's legs came as femur/tibia/tarsus pieces), plus red hair-fringe cards, chelicerae, eyes and two extras: a
ninth leg along the midline under the abdomen and a short stub. The native spider has eight legs: both extras and
the fringe cards that hang on them are deleted (EXTRA).
Bones: Thorax (root, pedicel -> head), Abdomen, Fang_L/R, per leg L1..L4 / R1..R4 (front to back) Femur, Tibia,
Tarsus. Leg joints per piece (work/leg_joints.json): hip = the piece's closest point to the body, knee = the top of
its centreline, foot = its farthest low point, ankle = 62 % of the way knee -> foot along the centreline.
Weights: legs by the closest point on their chain (4 cm blend at joints, 4 smoothing passes over mesh edges);
fringe cards copy the nearest leg vertex; the body blends Thorax -> Abdomen across the pedicel (6 cm); chelicerae
rigid on Fang_L/R; eyes and other small pieces on Thorax.
Args: none (reads work/step1.blend, writes work/rig_v1.blend)"""
import bpy, bmesh, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGS = {'R1': 8, 'R2': 1, 'R3': 9, 'R4': 7, 'L1': 6, 'L2': 5, 'L3': 4, 'L4': 3}
EXTRA = (2, 10)
PEDICEL_Y = 0.06
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)

# ---------------------------------------------------------------- delete the extras and their fringe cards
legv = {k: co[pv == p] for k, p in LEGS.items()}
allleg = np.concatenate([co[pv == p] for p in list(LEGS.values()) + list(EXTRA)])
alllab = np.concatenate([np.full((pv == p).sum(), p) for p in list(LEGS.values()) + list(EXTRA)])
kl = KDTree(len(allleg))
for i, c in enumerate(allleg):
    kl.insert(c, i)
kl.balance()
drop = set(EXTRA)
for p in range(1, pv.max() + 1):
    if p in LEGS.values() or p in EXTRA:
        continue
    c = co[pv == p].mean(0)
    near = alllab[kl.find(c)[1]]; d = kl.find(c)[2]
    if near in EXTRA and d < 0.12:
        drop.add(p)
bm = bmesh.new(); bm.from_mesh(me); lay = bm.verts.layers.int['piece']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in drop], context='VERTS')
bm.to_mesh(me); bm.free()
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
print('RIG deleted pieces', sorted(int(x) for x in drop), 'verts left', len(co))

# ---------------------------------------------------------------- leg joints
bodyv = co[pv == 0]
kb = KDTree(len(bodyv))
for i, c in enumerate(bodyv):
    kb.insert(c, i)
kb.balance()
J = {}
for leg, p in LEGS.items():
    c = co[pv == p]
    dist = np.array([kb.find(x)[2] for x in c])
    hip = c[np.argsort(dist)[:10]].mean(0)
    far = np.linalg.norm(c[:, :2] - hip[:2], axis=1)
    foot = c[np.argsort(-far)[:8]].mean(0); foot[2] = c[np.argsort(-far)[:30], 2].min()
    # centreline: bins along the horizontal hip -> foot direction
    dxy = (foot - hip)[:2]; L = np.linalg.norm(dxy); u = dxy / L
    t = ((c[:, :2] - hip[:2]) @ u) / L
    cl = [c[(t > a) & (t <= a + 0.05)].mean(0) for a in np.arange(0, 1.0, 0.05) if ((t > a) & (t <= a + 0.05)).sum() > 3]
    cl = np.array(cl)
    k = int(np.argmax(cl[:, 2])); knee = cl[k]
    rest = cl[k:]; seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.vstack([rest, foot]), axis=0), axis=1))]
    s = 0.62 * seg[-1]; j = int(np.searchsorted(seg, s)); j = min(max(j, 1), len(rest))
    pts = np.vstack([rest, foot]); a = (s - seg[j - 1]) / max(seg[j] - seg[j - 1], 1e-6)
    ankle = pts[j - 1] + (pts[j] - pts[j - 1]) * a
    J[leg] = [hip.tolist(), knee.tolist(), ankle.tolist(), foot.tolist()]
json.dump({k: [[round(x, 4) for x in p] for p in v] for k, v in J.items()}, open(os.path.join(HERE, 'work', 'leg_joints.json'), 'w'), indent=1)
head_front = Vector((float(bodyv[:, 0].mean()), float(bodyv[:, 1].min()) + 0.05, 0.32))
pedicel = Vector((0.02, PEDICEL_Y, float(np.median(bodyv[np.abs(bodyv[:, 1] - PEDICEL_Y) < 0.04, 2]))))
abd_end = Vector((0.03, float(bodyv[:, 1].max()) - 0.05, 0.40))

# ---------------------------------------------------------------- armature
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT'); eb = ad.edit_bones


def bone(name, h, t, parent=None, connect=False):
    b = eb.new(name); b.head = Vector(h); b.tail = Vector(t); b.parent = parent; b.use_connect = connect
    d = (b.tail - b.head).normalized()
    b.align_roll(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    return b


th = bone('Thorax', pedicel, head_front)
bone('Abdomen', pedicel, abd_end, th)
FANG = {}
for p in range(1, pv.max() + 1):
    c = co[pv == p]
    if len(c) and len(c) < 200 and c[:, 1].mean() < -0.45 and c[:, 2].mean() < 0.36:
        FANG.setdefault('L' if c[:, 0].mean() > 0.0 else 'R', []).append(p)
for s, ps in FANG.items():
    c = np.concatenate([co[pv == p] for p in ps])
    bone(f'Fang_{s}', c[np.argsort(-c[:, 2])[:10]].mean(0), c[np.argsort(c[:, 2])[:10]].mean(0), th)
for leg, (h, k, a, f) in J.items():
    fb = bone(f'Femur_{leg}', h, k, th)
    tb = bone(f'Tibia_{leg}', k, a, fb, True)
    bone(f'Tarsus_{leg}', a, f, tb, True)
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((len(co), len(names)))


def chain_weights(pts, p, blend):
    best = None
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1]); L = np.linalg.norm(b - a)
        t = np.clip((p - a) @ (b - a) / L / L, 0, 1); d = np.linalg.norm(p - (a + (b - a) * t))
        if best is None or d < best[0]:
            best = (d, i, t * L, L)
    _, i, s, L = best
    w = np.zeros(len(pts) - 1); w[i] = 1.0
    if i > 0 and s < blend:
        k = 0.5 * (1 - s / blend); w[i] -= k; w[i - 1] += k
    if i < len(pts) - 2 and s > L - blend:
        k = 0.5 * (1 - (L - s) / blend); w[i] -= k; w[i + 1] += k
    return w


for leg, p in LEGS.items():
    cols = [gi[f'{n}_{leg}'] for n in ('Femur', 'Tibia', 'Tarsus')]
    for i in np.where(pv == p)[0]:
        W[i, cols] = chain_weights(J[leg], co[i], 0.04)
adj = [[] for _ in range(len(co))]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
legmask = np.isin(pv, list(LEGS.values()))
for _ in range(4):
    W2 = W.copy()
    for i in np.where(legmask)[0]:
        if adj[i]:
            W2[i] = 0.5 * W[i] + 0.5 * W[adj[i]].mean(0)
    W = W2
for i in np.where(pv == 0)[0]:
    w = float(np.clip((co[i, 1] - (PEDICEL_Y - 0.03)) / 0.06, 0, 1))
    W[i, gi['Thorax']] = 1 - w; W[i, gi['Abdomen']] = w
klg = KDTree(int(legmask.sum())); li = np.where(legmask)[0]
for j, i in enumerate(li):
    klg.insert(co[i], j)
klg.balance()
fangp = {p: s for s, ps in FANG.items() for p in ps}
for p in range(1, pv.max() + 1):
    idx = np.where(pv == p)[0]
    if not len(idx) or p in LEGS.values():
        continue
    if p in fangp:
        W[idx] = 0; W[idx, gi[f'Fang_{fangp[p]}']] = 1; continue
    c = co[idx].mean(0); hit = klg.find(c)
    if hit[2] < 0.1:                                                     # fringe card: rigid on the nearest leg vertex
        W[idx] = W[li[hit[1]]]
    else:
        W[idx] = 0; W[idx, gi['Thorax' if c[1] < PEDICEL_Y else 'Abdomen']] = 1
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for n in names:
    body.vertex_groups.new(name=n)
for j, n in enumerate(names):
    for i in np.nonzero(W[:, j] > 1e-4)[0]:
        body.vertex_groups[n].add([int(i)], float(W[i, j]), 'REPLACE')
body.parent = rig; m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
print('RIG bones', len(names), 'fangs', {s: ps for s, ps in FANG.items()}, 'unweighted', int((W.sum(1) < 0.5).sum()))
for leg, j in J.items():
    print('RIG', leg, 'hip', np.round(j[0], 2), 'knee', np.round(j[1], 2), 'ankle', np.round(j[2], 2), 'foot', np.round(j[3], 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
