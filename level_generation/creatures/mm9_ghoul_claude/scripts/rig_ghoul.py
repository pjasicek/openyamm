"""Step C: MM9 skeleton (true-handed source; joints stay on MM9's, the hands were laid onto them) + weights. Bone heat on the body skin with a clean segment rig, then rules by part;
digits by connectivity onto MM9's own finger chains (no new bones); Bone01/Bone03 carry the flaps as in MM9; half-rotation helpers *_h at hips, knees, elbows, shoulders, neck,
head; hinge pivots moved to the outside of the bend. Args: <graft blend> <mm9 glb> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digits as DG, digits2 as D2
IN, MM9, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
bpy.ops.import_scene.gltf(filepath=MM9)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'MM9_Rig'
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o not in (body, rig): bpy.data.objects.remove(o)
bpy.context.view_layer.update()
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
print('JOINTS', len(J))
me = body.data
n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
B = 'Bip01 '
SEG = []
def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))
chain([B + 'Pelvis', B + 'Spine', B + 'Spine1', B + 'Spine2', B + 'Spine3', B + 'Neck', B + 'Head'], J[B + 'Head'] + np.array([0, 0, 0.2]))
for s in 'LR':
    SEG.append((B + f'{s} Clavicle', J[B + f'{s} Clavicle'], J[B + f'{s} UpperArm']))
    tip = J[B + f'{s} Hand'] + (J[B + f'{s} Finger1'] - J[B + f'{s} Hand']) * 1.6
    chain([B + f'{s} UpperArm', B + f'{s} Forearm', B + f'{s} Hand'], tip)
    toe = J[B + f'{s} Toe0'] + np.array([0.01, -0.12, 0.0])
    chain([B + f'{s} Thigh', B + f'{s} Calf', B + f'{s} Foot', B + f'{s} Toe0'], toe)
ad = bpy.data.armatures.new('heat'); hr = bpy.data.objects.new('heat', ad); bpy.context.scene.collection.objects.link(hr)
bpy.context.view_layer.objects.active = hr
for o in bpy.data.objects: o.select_set(o is hr)
bpy.ops.object.mode_set(mode='EDIT')
for nm, a, b in SEG:
    eb = ad.edit_bones.new(nm); eb.head = Vector(a); eb.tail = Vector(b)
bpy.ops.object.mode_set(mode='OBJECT')
skin = body.copy(); skin.data = me.copy(); skin.name = 'skin'; bpy.context.scene.collection.objects.link(skin)
bm = bmesh.new(); bm.from_mesh(skin.data); lay = bm.verts.layers.int['part']
oid = bm.verts.layers.int.new('oid')
bm.verts.ensure_lookup_table()
for v in bm.verts: v[oid] = v.index
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
oids = np.array([v[oid] for v in bm.verts])
bm.to_mesh(skin.data); bm.free()
for o in bpy.data.objects: o.select_set(False)
skin.select_set(True); hr.select_set(True); bpy.context.view_layer.objects.active = hr
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
bones = list(J)
bid = {b: i for i, b in enumerate(bones)}
W = np.zeros((n, len(bones)))
for v in skin.data.vertices:
    for g in v.groups:
        W[oids[v.index], bid[skin.vertex_groups[g.group].name]] = g.weight
print('heat: verts with no weight', int(((W.sum(1) == 0) & (pa == 0)).sum()), 'of', int((pa == 0).sum()))
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def only(m, b): W[m] = 0; W[m, bid[B + b]] = 1
z = P[:, 2]; y = P[:, 1]
only((pa == 10) | (pa == 12) | (pa == 13), 'Head')
# neck tube and its root
hd = (pa == 0) & (z > 0.52) & (np.abs(P[:, 0]) < 0.14)
wh = sstep(z - (0.623 + 0.33 * y), -0.03, 0.03)
ar = sstep(z, 0.56, 0.62)
tube = np.zeros_like(W); tube[:, bid[B + 'Neck']] = 1 - wh; tube[:, bid[B + 'Head']] = wh
W[hd] = (W[hd].T * (1 - ar[hd])).T + (tube[hd].T * ar[hd]).T
# hair: rigid with the head at the top, the back's at the tips
h_ = pa == 11
whr = sstep(z, 0.50, 0.80)
W[h_] = 0
W[h_, bid[B + 'Head']] = whr[h_]; W[h_, bid[B + 'Spine3']] = (1 - whr)[h_]
# studs and plate copy the nearest skin
from mathutils.kdtree import KDTree
sk = np.nonzero(pa == 0)[0]
kd = KDTree(len(sk))
for i in sk: kd.insert(P[i], int(i))
kd.balance()
st = np.nonzero(pa == 3)[0]
# whole pieces: weights of the skin at the piece's centre, so a stud stays rigid
seen = np.zeros(n, bool)
for i in st:
    if seen[i]: continue
    stack = [i]; seen[i] = True; cc = [i]
    while stack:
        x = stack.pop()
        for y2 in nbr[x]:
            if pa[y2] == 3 and not seen[y2]: seen[y2] = True; stack.append(y2); cc.append(y2)
    W[cc] = W[kd.find(P[cc].mean(0))[1]]
# flaps: pelvis at the belt, the MM9 flap bones below it, rigid as MM9's
for pid, bn in ((6, 'Bone01'), (7, 'Bone03')):
    m = pa == pid
    b = sstep(0.08 - z, 0.0, 0.10)
    W[m] = 0; W[m, bid[B + 'Pelvis']] = (1 - b)[m]; W[m, bid[bn]] = b[m]
# digits by connectivity onto MM9's chains
CH = lambda s: [[f'{s} Finger0', f'{s} Finger01', f'{s} Finger02'], [f'{s} Finger1', f'{s} Finger11', f'{s} Finger12'], [f'{s} Finger2', f'{s} Finger21', f'{s} Finger22'], [f'{s} Finger3', f'{s} Finger31', f'{s} Finger32'], [f'{s} Finger41', f'{s} Finger42']]
for s, sx in (('L', 1), ('R', -1)):
    root = J[B + f'{s} Hand']; fw = root - J[B + f'{s} Forearm']; fw = fw / np.linalg.norm(fw)
    ax = (P - root) @ fw
    region = (np.linalg.norm(P - root, axis=1) < 0.5) & (np.sign(P[:, 0]) == sx) & (np.abs(P[:, 0]) > 0.2) & (ax > -0.10) & (pa == 0)
    seeds = [i for i in np.nonzero(region)[0] if ax[i] < -0.085]
    d = DG.geodesic(P, nbr, seeds, region)
    ids = np.nonzero(np.isfinite(d))[0]
    br = D2.digit_tree(d, nbr, ids, 0.03)
    br.sort(key=lambda b: b['base'])
    print('DIGITS', s, [(round(b['base'], 3), round(b['tip'] - b['base'], 3), len(b['verts'])) for b in br])
    assert len(br) == 5
    th = br[0]
    tips = {id(b): P[b['tipv']] for b in br}
    # across the palm by the base of the digit, from the thumb side: MM9's fingers run index to pinky along +z of the source (Blender -y to +y)
    rest = sorted(br[1:], key=lambda b: P[np.array(b['verts'])][:, 1].mean())
    order = [th] + rest
    assert len({id(b) for b in order}) == 5, 'digit order'
    for ch, b in zip(CH(s), order):
        jt = np.array([J[B + c] for c in ch])
        vs = np.array(b['verts'])
        if ch[0].endswith('Finger0'):
            vs = vs[d[vs] > b['tip'] - 0.15]
        lo = d[vs].min()
        # distance along MM9's chain: nearest segment; the last bone runs on to the tip
        ext = np.vstack([jt, jt[-1] + (jt[-1] - jt[-2]) * 4])
        seg = np.zeros(len(vs), int)
        for k, q in enumerate(P[vs]):
            bestd = 1e9
            for i in range(len(ext) - 1):
                a_, b_ = ext[i], ext[i + 1]; t = np.clip((q - a_) @ (b_ - a_) / ((b_ - a_) @ (b_ - a_)), 0, 1)
                dd = np.linalg.norm(q - (a_ + t * (b_ - a_)))
                if dd < bestd: bestd = dd; seg[k] = i; tb = t
            seg[k] = min(seg[k], len(jt) - 1)
        W[vs] = 0
        hw = 1 - sstep(d[vs] - lo, 0.0, 0.02)
        for k, c in enumerate(ch):
            W[vs[seg == k], bid[B + c]] = (1 - hw[seg == k])
        W[vs, bid[B + f'{s} Hand']] = hw
        # a little blend across each joint along the digit
        for _ in range(2):
            avg = W[vs].copy()
            for i, v in enumerate(vs):
                nb = [q for q in nbr[v] if q in set(vs.tolist())] if False else [q for q in nbr[v]]
                avg[i] = W[nb].mean(0) * 0.35 + W[v] * 0.65
            W[vs] = avg
# light smoothing on the skin, not on digits
hand_b = [bid[k] for k in bid if 'Finger' in k or k.endswith(' Hand')]
ff = W[:, hand_b].sum(1) > 0.5
for _ in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    m = (pa == 0) & ~ff
    W[m] = 0.6 * W[m] + 0.4 * avg[m]
# ---------- half-rotation helpers, keyed by half_keys.py
HELP = (('L Thigh', ('Pelvis', 'Spine', 'Spine1')), ('R Thigh', ('Pelvis', 'Spine', 'Spine1')), ('L Calf', ('L Thigh',)), ('R Calf', ('R Thigh',)), ('L Forearm', ('L UpperArm',)), ('R Forearm', ('R UpperArm',)),
        ('L UpperArm', ('L Clavicle', 'Spine3', 'Spine2')), ('R UpperArm', ('R Clavicle', 'Spine3', 'Spine2')), ('Head', ('Neck',)), ('Neck', ('Spine3',)))
parents = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
Mi = rig.matrix_world.inverted()
# hinge pivots toward the outside of the bend (mummy's lesson): knee and elbow back, hip forward
SH = {'L Calf': (0, 0.03, 0), 'R Calf': (0, 0.03, 0), 'L Forearm': (0, 0.015, 0), 'R Forearm': (0, 0.015, 0), 'L Thigh': (0, -0.025, 0), 'R Thigh': (0, -0.025, 0)}
for k, v in SH.items():
    e = eb[B + k]; d_ = Mi.to_3x3() @ Vector(v)
    e.use_connect = False
    for c in e.children: c.use_connect = False
    e.head += d_; e.tail += d_
for c, ps in HELP:
    h = eb.new(B + c + '_h'); t = eb[B + c]
    h.head = t.head; h.tail = t.tail; h.roll = t.roll; h.parent = eb[parents[B + c]]; h.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
allb = bones + [B + c + '_h' for c, _ in HELP]
bid = {b: i for i, b in enumerate(allb)}
W = np.c_[W, np.zeros((n, len(HELP)))]
for c, ps in HELP:
    ci = bid[B + c]; pi = [bid[B + p] for p in ps]; hi = bid[B + c + '_h']
    wc = W[:, ci]; wp = W[:, pi].sum(1); tot = wc + wp
    m = (wc > 1e-3) & (wp > 1e-3) & (pa == 0)
    t = wc[m] / tot[m]
    scale = np.maximum(1 - 2 * t, 0)
    for p in pi: W[m, p] = W[m, p] * scale
    W[m, ci] = tot[m] * np.maximum(2 * t - 1, 0)
    W[m, hi] = tot[m] * (1 - np.abs(2 * t - 1))
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(allb)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
print('zero weight verts', int((W.sum(1) < 0.5).sum()))
for b in allb: body.vertex_groups.new(name=b)
nzi, nzj = np.nonzero(W)
for i, j in zip(nzi, nzj):
    body.vertex_groups[allb[j]].add([int(i)], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bid[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = rig; body.matrix_parent_inverse = rig.matrix_world.inverted()
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIGGED', n, len(allb))
