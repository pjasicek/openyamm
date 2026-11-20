"""Step C: MM9 skeleton (true-handed source, joints unchanged: the mesh was fitted onto them) + weights.
Bone heat on a closed-skin copy with a clean segment rig, then rules by part; fingers by connectivity with 15 new bones per side (rest frame of MM9's mitten bone).
Args: <graft blend> <mm9 glb> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digits as DG
IN, MM9, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'MM9_Rig'
if rig.animation_data: rig.animation_data.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in list(bpy.data.objects):
    if o not in (body, rig) : bpy.data.objects.remove(o)
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
# ---------- temp segment rig + bone heat on the skin parts
SEG = []
def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))
B = 'Bip01 '
chain([B + 'Pelvis', B + 'Spine', B + 'Spine1', B + 'Spine2', B + 'Spine3', B + 'Neck', B + 'Head'], J[B + 'Head'] + np.array([0, 0, 0.2]))
for s in 'LR':
    chain([B + 'Neck'], None) if False else None
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
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in (2, 3, 11, 12, 13)], context='VERTS')
print('skin verts', len(bm.verts))
oids = np.array([v[oid] for v in bm.verts])
bm.to_mesh(skin.data); bm.free()
for o in bpy.data.objects: o.select_set(False)
skin.select_set(True); hr.select_set(True); bpy.context.view_layer.objects.active = hr
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
names = [g.name for g in skin.vertex_groups]
print('heat groups', len(names))
bones = list(J)
bid = {b: i for i, b in enumerate(bones)}
W = np.zeros((n, len(bones)))
cnt = 0
for v in skin.data.vertices:
    for g in v.groups:
        W[oids[v.index], bid[skin.vertex_groups[g.group].name]] = g.weight; cnt += 1
tot = W.sum(1)
print('heat: verts with no weight', int(((tot == 0) & np.isin(pa, (0, 1, 4, 5, 10))).sum()), 'of', int(np.isin(pa, (0, 1, 4, 5, 10)).sum()))
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)
np.save(OUT + '.heat.npy', W)


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- rules by part
def only(m, b): W[m] = 0; W[m, bid[B + b]] = 1
z = P[:, 2]
hd = pa >= 10
# the head/neck band follows a plane from under the chin to the nape, so the jaw stays rigid on the head
w_head = sstep(z - (0.815 + 0.25 * P[:, 1]), -0.022, 0.022)
W[hd] = 0
W[hd, bid[B + 'Head']] = w_head[hd]; W[hd, bid[B + 'Neck']] = 1 - w_head[hd]
only(pa == 12, 'Head'); only(pa == 13, 'Head')
only(pa == 4, 'R Calf')
# upper neck skin on the body: Neck over Spine3
# loose pieces copy the nearest skin (rope, knot, tatter)
sk = np.nonzero(np.isin(pa, (0, 1)))[0]
Sk = P[sk]
from mathutils.kdtree import KDTree
kd = KDTree(len(sk))
for i, p in zip(sk, Sk): kd.insert(p, int(i))
kd.balance()
for i in np.nonzero(np.isin(pa, (2, 3)))[0]:
    W[i] = W[kd.find(P[i])[1]]
# tatter: hangs from the belt: pelvis at the top, a share of the thigh of its own side at the hem, so a raised thigh lifts the cloth instead of passing through it
tt = np.nonzero(pa == 2)[0]
ztop, zbot = P[tt, 2].max(), P[tt, 2].min()
for i in tt:
    h = float(sstep(np.array(ztop - P[i, 2]), 0.03, ztop - zbot))
    side = float(sstep(np.array(abs(P[i, 0])), 0.0, 0.07))
    s_ = 'L' if P[i, 0] > 0 else 'R'
    W[i] = 0
    wt = 0.8 * h * side
    W[i, bid[B + f'{s_} Thigh']] = wt
    W[i, bid[B + 'Pelvis']] = (1 - wt)
# ---------- fingers by connectivity (left hand; the right is its mirror image)
new_bones = {}
J2 = dict(J)
FN = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
info = {}
for s, sx in (('L', 1), ('R', -1)):
    root = J[B + f'{s} Hand']
    fw = root - J[B + f'{s} Forearm']; fw = fw / np.linalg.norm(fw)
    region = (np.linalg.norm(P - root, axis=1) < 0.30) & (np.sign(P[:, 0]) == sx) & (pa == 0) & ((P - root) @ fw > -0.012)
    seeds = [i for i in np.nonzero(region)[0] if np.linalg.norm(P[i] - root) < 0.04]
    d = DG.geodesic(P, nbr, seeds, region)
    ids = np.nonzero(np.isfinite(d))[0]
    br = DG.branches(d, nbr, ids, 0.028, 5)
    br.sort(key=lambda b: -(b['tip'] - b['base']))
    print('BRANCHES', s, [(round(b['tip'] - b['base'], 3), len(b['verts'])) for b in br[:7]])
    br = br[:5]
    assert len(br) == 5
    tips = np.array([P[b['tipv']] for b in br])
    # thumb: the tip farthest from the mean of the others; order the rest across the hand from the thumb
    dd = np.linalg.norm(tips[:, None] - tips[None], axis=2).sum(1)
    th = int(np.argmax(dd))
    o = sorted([i for i in range(5) if i != th], key=lambda i: np.linalg.norm(tips[i] - tips[th]))
    order = [th] + o
    info[s] = (br, order, d)
    for f, bi in zip(FN, order):
        b = br[bi]
        C = DG.centreline(P, d, b['verts'], 10, b['base'])
        fr = (0.0, 0.42, 0.72) if f != 'Thumb' else (0.0, 0.45, 0.75)
        jt = [DG.along(C, q) for q in fr]; tip = C[-1]
        for k in range(3):
            new_bones[B + f'{s} {f}{k + 1}'] = (jt[k], jt[k + 1] if k < 2 else tip, B + (f'{s} Hand' if k == 0 else f'{s} {f}{k}'), B + f'{s} Finger{0 if f == "Thumb" else 1}')
        # weights along the chain
        vs = np.array(b['verts'])
        t = d[vs]
        lo, hi = t.min(), t.max()
        L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.array(jt + [tip]), axis=0), axis=1))]
        L = L / L[-1] * (hi - lo) + lo
        wk = np.stack([1 - sstep(t, L[1] - 0.006, L[1] + 0.006), sstep(t, L[1] - 0.006, L[1] + 0.006) * (1 - sstep(t, L[2] - 0.005, L[2] + 0.005)), sstep(t, L[2] - 0.005, L[2] + 0.005)], 1)
        wh = 1 - sstep(t, lo - 0.004, lo + 0.01)      # palm share at the knuckle
        info.setdefault('w', {})[(s, f)] = (vs, wk, wh)
# bones
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
Mi = rig.matrix_world.inverted()
for nm, (a, b, par, tmpl) in new_bones.items():
    e = eb.new(nm); t = eb[tmpl]
    e.head = Mi @ Vector(a)
    # the MM9 mitten frame, so clips_mm9 finger_alias can copy its rotation
    e.tail = e.head + (t.tail - t.head); e.roll = t.roll
    e.parent = eb[par]; e.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
allb = bones + list(new_bones)
bid = {b: i for i, b in enumerate(allb)}
W = np.c_[W, np.zeros((n, len(new_bones)))]
for (s, f), (vs, wk, wh) in info['w'].items():
    hb = bid[B + f'{s} Hand']
    # keep the palm weights already heat-solved for the hand set, moved all to Hand first
    for k in range(3):
        W[vs, bid[B + f'{s} {f}{k + 1}']] = wk[:, k] * (1 - wh)
    W[vs, :len(bones)] = 0
    W[vs, hb] = wh
# everything past the wrist that is no finger stays on the hand; light smoothing on the skin
for _ in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    m = np.isin(pa, (0, 1, 5))
    ff = W[:, len(bones):].sum(1) > 0
    m &= ~ff
    W[m] = 0.6 * W[m] + 0.4 * avg[m]
# rope: a tube must not shear across its section: its weights are smoothed along the rope until a section moves as one; knot and cords hang rigid from it
rope = np.nonzero(pa == 3)[0]
for _ in range(40):
    W[rope] = np.array([W[nbr[i]].mean(0) if nbr[i] else W[i] for i in rope])
# ---------- half-rotation helpers (cat lesson): the skin over a joint follows an arc, not a chord
HELP = (('L Thigh', ('Pelvis', 'Spine')), ('R Thigh', ('Pelvis', 'Spine')), ('L Calf', ('L Thigh',)), ('R Calf', ('R Thigh',)), ('L Forearm', ('L UpperArm',)), ('R Forearm', ('R UpperArm',)),
        ('L UpperArm', ('L Clavicle', 'Spine3')), ('R UpperArm', ('R Clavicle', 'Spine3')), ('Head', ('Neck',)), ('Neck', ('Spine3',)))
parents = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for c, ps in HELP:
    h = eb.new(B + c + '_h'); t = eb[B + c]
    h.head = t.head; h.tail = t.tail; h.roll = t.roll; h.parent = eb[parents[B + c]]; h.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
allb += [B + c + '_h' for c, _ in HELP]
bid = {b: i for i, b in enumerate(allb)}
W = np.c_[W, np.zeros((n, len(HELP)))]
for c, ps in HELP:
    ci = bid[B + c]; pi = [bid[B + p] for p in ps]; hi = bid[B + c + '_h']
    wc = W[:, ci]; wp = W[:, pi].sum(1); tot = wc + wp
    m = (wc > 1e-3) & (wp > 1e-3)
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
for i in range(n):
    for j in np.nonzero(W[i])[0]:
        body.vertex_groups[allb[j]].add([i], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bid[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = rig; body.matrix_parent_inverse = rig.matrix_world.inverted()
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIGGED', n, len(allb))
