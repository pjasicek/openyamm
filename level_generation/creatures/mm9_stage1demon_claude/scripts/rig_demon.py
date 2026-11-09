"""Step C: MM9 skeleton (true-handed source; joints stay on MM9's except the jaw pivot, moved to our mouth corners) + weights
(from mm9_ghoul_claude/scripts/rig_ghoul.py). Bone heat on the body skin with a clean segment rig, then rules by part:
armour shells copy the nearest skin, small pieces are rigid with the skin under their base, the tail and the rebuilt digits
follow MM9's chains by projection, the head splits into skull (Xhead), lower jaw (Xjaw, below the half-gape plane through
the hinge), tongue (Xtongpiv/Xtong), teeth with the shell under them, and blends into the neck behind the hinge.
Half-rotation helpers *_h at hips, knees, elbows, shoulders; hinge pivots at the outside of the bend.
Args: <reduced blend> <mm9 true glb> <config json> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
IN, MM9, CFG, OUT = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))['rig']
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
B = 'Bip01 '
H = np.array(cfg['hinge'])
# the jaw pivot goes to our mouth corners (children stay where they are)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted()
e = eb['Xjawpiv']; d_ = Mi @ Vector(H) - e.head
for c in e.children: c.use_connect = False
e.use_connect = False; e.head += d_; e.tail += d_
bpy.ops.object.mode_set(mode='OBJECT')
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
print('JOINTS', len(J), 'jawpiv', J['Xjawpiv'].round(3))
me = body.data; n = len(me.vertices)
P = np.array([v.co[:] for v in me.vertices])
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
dg_ = np.zeros(n, int); me.attributes['digit'].data.foreach_get('value', dg_)
nbr = [[] for _ in range(n)]
for ed in me.edges:
    a, b = ed.vertices; nbr[a].append(b); nbr[b].append(a)
SEG = []


def chain(names, tip=None):
    for a, b in zip(names[:-1], names[1:]): SEG.append((a, J[a], J[b]))
    if tip is not None: SEG.append((names[-1], J[names[-1]], tip))


chain([B + 'Pelvis', B + 'Spine', B + 'Spine1', B + 'Spine2', B + 'Neck', 'Xneckbase', 'Xneckpiv', 'XneckA', 'Xheadpiv', 'Xhead'], J['XheadB'])
chain(['Xtailbase', 'Xtailpiv', 'XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailE'], J['XtailE'] + (J['XtailE'] - J['XtailD']) * 0.6)
for s in 'LR':
    SEG.append((B + f'{s} Clavicle', J[B + f'{s} Clavicle'], J[B + f'{s} UpperArm']))
    chain([B + f'{s} UpperArm', B + f'{s} Forearm', B + f'{s} Hand'], J[B + f'{s} Hand'] + (J[B + f'{s} Finger2'] - J[B + f'{s} Hand']) * 1.3)
    chain([B + f'{s} Thigh', B + f'{s} Calf', B + f'{s} Foot'], J[B + f'{s} Toe11'])
    for t in '012':
        a, b_ = J[B + f'{s} Toe{t}1'], J[B + f'{s} Toe{t}2']
        chain([B + f'{s} Toe{t}1', B + f'{s} Toe{t}2'], b_ + (b_ - a) * 1.2)
ad = bpy.data.armatures.new('heat'); hr = bpy.data.objects.new('heat', ad); bpy.context.scene.collection.objects.link(hr)
bpy.context.view_layer.objects.active = hr
for o in bpy.data.objects: o.select_set(o is hr)
bpy.ops.object.mode_set(mode='EDIT')
for nm, a, b in SEG:
    x = ad.edit_bones.new(nm); x.head = Vector(a); x.tail = Vector(b) if np.linalg.norm(b - a) > 1e-3 else Vector(a + np.array([0, 0, 0.02]))
bpy.ops.object.mode_set(mode='OBJECT')
skin = body.copy(); skin.data = me.copy(); skin.name = 'skin'; bpy.context.scene.collection.objects.link(skin)
bm = bmesh.new(); bm.from_mesh(skin.data); lay = bm.verts.layers.int['part']
oid = bm.verts.layers.int.new('oid'); bm.verts.ensure_lookup_table()
for v in bm.verts: v[oid] = v.index
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
oids = np.array([v[oid] for v in bm.verts]); bm.to_mesh(skin.data); bm.free()
for o in bpy.data.objects: o.select_set(False)
skin.select_set(True); hr.select_set(True); bpy.context.view_layer.objects.active = hr
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
bones = list(J); bid = {b: i for i, b in enumerate(bones)}
W = np.zeros((n, len(bones)))
for v in skin.data.vertices:
    for g in v.groups: W[oids[v.index], bid[skin.vertex_groups[g.group].name]] = g.weight
zero = (W.sum(1) == 0) & (pa == 0)
print('heat: skin verts with no weight', int(zero.sum()), 'of', int((pa == 0).sum()))
bpy.data.objects.remove(skin); bpy.data.objects.remove(hr)


def seg_dist(Q, a, b):
    ab = b - a; t = np.clip((Q - a) @ ab / max(ab @ ab, 1e-12), 0, 1)
    return np.linalg.norm(Q - a - np.outer(t, ab), axis=1)


if zero.any():   # heat failures: nearest segment
    D = np.stack([seg_dist(P[zero], a, b) for _, a, b in SEG], 1)
    for i, k in zip(np.nonzero(zero)[0], D.argmin(1)): W[i, bid[SEG[k][0]]] = 1


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


sk = np.nonzero(pa == 0)[0]
kd = KDTree(len(sk))
for i in sk: kd.insert(P[i], int(i))
kd.balance()


def comps_of(mask):
    seen = np.zeros(n, bool); out = []
    for i in np.nonzero(mask)[0]:
        if seen[i]: continue
        st = [i]; seen[i] = True; cc = [i]
        while st:
            x = st.pop()
            for y in nbr[x]:
                if mask[y] and not seen[y]: seen[y] = True; st.append(y); cc.append(y)
        out.append(np.array(cc))
    return out


# armour shells (1): per vertex from the nearest skin, then smoothed inside each shell; the palm takes the hand
for i in np.nonzero(pa == 1)[0]: W[i] = W[kd.find(P[i])[1]]
for s in 'LR':
    root = J[B + f'{s} Hand']; fw = root - J[B + f'{s} Forearm']; fw /= np.linalg.norm(fw)
    m = (pa == 1) & (np.linalg.norm(P - root, axis=1) < 0.3)
    w = sstep((P[m] - root) @ fw, -0.06, 0.02)
    W[m] = W[m] * (1 - w[:, None]); W[np.nonzero(m)[0], bid[B + f'{s} Hand']] += w
for cc in comps_of(pa == 1):
    for _ in range(3):
        W[cc] = 0.5 * W[cc] + 0.5 * np.array([W[[q for q in nbr[i] if pa[q] == 1] or [i]].mean(0) for i in cc])
# small pieces (2): rigid with the skin under the piece's base (its vertex nearest the skin)
for cc in comps_of(pa == 2):
    dd = [kd.find(P[i]) for i in cc]; k = int(np.argmin([x[2] for x in dd]))
    W[cc] = W[dd[k][1]]
# tail (4): projection onto MM9's tail chain, root blended into the skin's own weights
TC = ['Xtailbase', 'Xtailpiv', 'XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailE']
C9 = np.array([J[k] for k in TC]); C9 = np.vstack([C9, C9[-1] + (C9[-1] - C9[-2]) * 2])
L9 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C9, axis=0), axis=1))]
tm = np.nonzero(pa == 4)[0]
for i in tm:
    best = (1e9, 0, 0)
    for k in range(len(C9) - 1):
        a, b = C9[k], C9[k + 1]; ab = b - a; t = float(np.clip((P[i] - a) @ ab / (ab @ ab), 0, 1))
        dd = np.linalg.norm(P[i] - a - t * ab)
        if dd < best[0]: best = (dd, k, t)
    _, k, t = best; s = L9[k] + t * (L9[k + 1] - L9[k])
    row = np.zeros(len(bones)); kb = min(k, len(TC) - 1)
    # blend across each joint over 30 % of the shorter neighbouring segment
    row[bid[TC[kb]]] = 1
    if k < len(TC) - 1 and t > 0.7: f = (t - 0.7) / 0.6; row[bid[TC[kb]]] = 1 - f; row[bid[TC[min(kb + 1, len(TC) - 1)]]] += f
    if k > 0 and t < 0.3: f = (0.3 - t) / 0.6; row[bid[TC[kb]]] = 1 - f; row[bid[TC[kb - 1]]] += f
    wr = sstep(s, cfg['tail_root'][0], cfg['tail_root'][1])
    W[i] = row * wr + W[kd.find(P[i])[1]] * (1 - wr)
# digits (5): along MM9's own chain, root ring in the hand
for i in np.nonzero(pa == 5)[0]:
    s = 'R' if P[i, 0] < 0 else 'L'; f = str(dg_[i] % 10)
    ch = [B + f'{s} Finger{f}', B + f'{s} Finger{f}1', B + f'{s} Finger{f}2']
    jt = np.array([J[c] for c in ch]); u0 = (jt[1] - jt[0]) / np.linalg.norm(jt[1] - jt[0])
    a0 = (P[i] - jt[0]) @ u0
    row = np.zeros(len(bones))
    u1 = (jt[2] - jt[1]) / np.linalg.norm(jt[2] - jt[1]); a1 = (P[i] - jt[1]) @ u1
    u2 = u1; a2 = (P[i] - jt[2]) @ u2
    bl = cfg['digit_blend']
    w0 = sstep(a0, -bl, bl); w1 = sstep(a1, -bl, bl); w2 = sstep(a2, -bl, bl)
    row[bid[B + f'{s} Hand']] = 1 - w0; row[bid[ch[0]]] = w0 - w1; row[bid[ch[1]]] = w1 - w2; row[bid[ch[2]]] = w2
    W[i] = np.clip(row, 0, 1)
# ---- head
hm = np.isin(pa, (10, 12, 13, 14))
y, z = P[:, 1], P[:, 2]
ang = np.degrees(np.arctan2(z - H[2], -(y - H[1])))           # elevation seen from the hinge, forward = 0
jaw = (pa == 10) & (y < H[1] + cfg['jaw_back']) & (ang < cfg['gape_split'])
jw = sstep(cfg['gape_split'] - ang, 0, cfg['jaw_blend_deg'])    # soft at the lips' corner wedge
head_row = np.zeros(len(bones)); head_row[bid['Xhead']] = 1
jaw_row = np.zeros(len(bones)); jaw_row[bid['Xjaw']] = 1
for i in np.nonzero(pa == 10)[0]:
    W[i] = head_row
for i in np.nonzero(jaw)[0]:
    ww = jw[i] * sstep(H[1] + cfg['jaw_back'] - y[i], 0, 0.04)
    W[i] = jaw_row * ww + head_row * (1 - ww)
# tongue
tg = np.nonzero(pa == 14)[0]
a_ = J['Xtong'] - J['Xtongpiv']
for i in tg:
    t = (P[i] - J['Xtongpiv']) @ a_ / (a_ @ a_)
    w = sstep(t, 0.6, 1.1); row = np.zeros(len(bones)); row[bid['Xtongpiv']] = 1 - w; row[bid['Xtong']] = w
    W[i] = row
# eyes rigid with the skull
for i in np.nonzero(pa == 13)[0]: W[i] = head_row
# teeth: rigid with the shell under each tooth's root
sh = np.nonzero(pa == 10)[0]; ks = KDTree(len(sh))
for i in sh: ks.insert(P[i], int(i))
ks.balance()
for cc in comps_of(pa == 12):
    dd = [ks.find(P[i]) for i in cc]; k = int(np.argmin([x[2] for x in dd]))
    r = W[dd[k][1]]; W[cc] = (jaw_row if r[bid['Xjaw']] > 0.5 else head_row)
# behind the hinge the head blends into the neck skin (the cranium dome and the throat lie in the hump)
for i in np.nonzero((pa == 10) & ~jaw)[0]:
    wn = sstep(y[i] - H[1], cfg['neck_blend'][0], cfg['neck_blend'][1])
    if wn > 0: W[i] = W[i] * (1 - wn) + W[kd.find(P[i])[1]] * wn
# light smoothing on the skin and the head shell
for _ in range(2):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    m = np.isin(pa, (0, 10)) & ~jaw
    W[m] = 0.6 * W[m] + 0.4 * avg[m]
# ---------- half-rotation helpers (keyed by half_keys.py) and hinge pivots
HELP = (('L Thigh', ('Pelvis', 'Spine', 'Spine1')), ('R Thigh', ('Pelvis', 'Spine', 'Spine1')), ('L Calf', ('L Thigh',)), ('R Calf', ('R Thigh',)),
        ('L Forearm', ('L UpperArm',)), ('R Forearm', ('R UpperArm',)), ('L UpperArm', ('L Clavicle', 'Spine2', 'Neck')), ('R UpperArm', ('R Clavicle', 'Spine2', 'Neck')))
parents = {b.name: (b.parent.name if b.parent else None) for b in rig.data.bones}
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones; Mi = rig.matrix_world.inverted()
for k, v in cfg['pivots'].items():
    x = eb[B + k]; d_ = Mi.to_3x3() @ Vector(v)
    x.use_connect = False
    for c in x.children: c.use_connect = False
    x.head += d_; x.tail += d_
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
    m = (wc > 1e-3) & (wp > 1e-3) & np.isin(pa, (0, 1))
    t = wc[m] / tot[m]; scale = np.maximum(1 - 2 * t, 0)
    for p in pi: W[m, p] = W[m, p] * scale
    W[m, ci] = tot[m] * np.maximum(2 * t - 1, 0); W[m, hi] = tot[m] * (1 - np.abs(2 * t - 1))
order = np.argsort(-W, axis=1)
for i in range(n):
    keep = order[i, :4]; row = np.zeros(len(allb)); row[keep] = W[i, keep]; row[row < 0.015] = 0
    W[i] = row / max(row.sum(), 1e-9)
print('zero weight verts', int((W.sum(1) < 0.5).sum()), 'jaw verts', int(jaw.sum()))
for b in allb: body.vertex_groups.new(name=b)
nzi, nzj = np.nonzero(W)
for i, j in zip(nzi, nzj): body.vertex_groups[allb[j]].add([int(i)], float(W[i, j]), 'REPLACE')
for g in list(body.vertex_groups):
    if not np.any(W[:, bid[g.name]] > 0): body.vertex_groups.remove(g)
body.parent = rig; body.matrix_parent_inverse = rig.matrix_world.inverted()
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIGGED', n, len(allb))
