"""Symmetric lower-face skin weights (user review r10, 2026-11-04). After jaw_mirror3.py the bind shape is symmetric, but in the
viewer's Standing pose (head turned and rolled by MM9's stand clip) her right jaw still read as a straight diagonal: the narrow
side's cheek and jaw carried 13-21 % Bip01 R Clavicle at 1.71-1.73 m where the fuller side had 2-5 % L Clavicle, so that side lagged
behind the head. Two steps on the head's skin shell (the head component holding the nose) and the body neck within 4 cm of the
neck seam:
1. the narrow side (master +x for HOF1) takes the mirror image of the fuller side's weights: inverse-distance mean of the 3
   nearest fuller-side vertices to the vertex's mirrored position, bone names mirrored by rest position (the bone whose mirrored
   head lies nearest: L/R and the two braid chains), blended with the same smooth region weight as jaw_mirror3.py (upper edge
   Y1-0.02..Y1, midline T0..T0+15 deg, back T1-20..T1 deg, body neck faded over 4 cm below the seam);
2. on both sides, clavicle weight on the head shell fades to 0 from 1.67 m up to 1.70 m (export height; smoothstep), the removed
   weight going to Bip01 Head: a shrug no longer pulls the cheeks;
3. on both sides, Neck and Clavicle weight on the head shell fades from 5 mm above the neck seam to 0 at 25 mm (smoothstep on the
   distance to the seam), the removed weight going to Bip01 Head: the jaw keeps its shape when the head turns against the neck.
Args: <in blend> <out blend> [y1 1.748] [t0 12] [t1 135] [export head y 1.697] [fuller side -|+]"""
import bpy, bmesh, sys, math
from mathutils import Vector
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
f = lambda i, d: float(a[i]) if len(a) > i else d
Y1, T0, T1, HEADY = f(2, 1.748), f(3, 12.0), f(4, 135.0), f(5, 1.697)
full = -1 if (a[6] if len(a) > 6 else '-') == '-' else 1
NECK = 0.04
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent; mw = ob.matrix_world
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
hb = next(b for b in rig.pose.bones if b.name.endswith('Head')); off = HEADY - (rig.matrix_world @ hb.head).z
me = ob.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
ishead = lambda f_: f_[lh] and not f_[lk]
hv = {v.index for f_ in bm.faces if ishead(f_) for v in f_.verts}
W = [mw @ v.co for v in bm.verts]
fr = [i for i in hv if 1.70 - off < W[i].z < 1.78 - off]
nose = min(fr, key=lambda i: W[i].y)
comp = {nose}; st = [bm.verts[nose]]
while st:
    v = st.pop()
    for e in v.link_edges:
        o = e.other_vert(v)
        if o.index in hv and o.index not in comp: comp.add(o.index); st.append(o)
cx = W[nose].x
band = [i for i in comp if 1.60 - off < W[i].z < Y1 - off]
cy = 0.5 * (min(W[i].y for i in band) + max(W[i].y for i in band))
def ang(p): return math.degrees(math.atan2(abs(p.x - cx), -(p.y - cy)))
def ss(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
seam = [i for i in comp if any(not ishead(f_) for f_ in bm.verts[i].link_faces) and W[i].z + off < 1.71]
kds = KDTree(len(seam))
for k, i in enumerate(seam): kds.insert(W[i], k)
kds.balance()
neckv = {v.index for f_ in bm.faces if not f_[lh] and all(kds.find(W[u.index])[2] < NECK + 0.01 and W[u.index].z + off < 1.71
                                                        for u in f_.verts) for v in f_.verts}
bm.free()
# bone mirror by rest head position
bones = rig.data.bones
bpos = {b.name: rig.matrix_world @ b.head_local for b in bones}
def mirror_bone(n):
    p = bpos[n]; m = Vector((2 * cx - p.x, p.y, p.z))
    return min(bpos, key=lambda k: (bpos[k] - m).length)
gidx = {g.name: g.index for g in ob.vertex_groups}
gname = {g.index: g.name for g in ob.vertex_groups}
mir = {}
for n in gidx:
    if n in bpos:
        m = mirror_bone(n)
        if m not in gidx: ob.vertex_groups.new(name=m); gidx[m] = ob.vertex_groups[m].index; gname[gidx[m]] = m
        mir[n] = m
    else:
        mir[n] = n
def weights(i): return {gname[g.group]: g.weight for g in me.vertices[i].groups if g.weight > 0}
pool = [i for i in (comp | neckv) if (W[i].x - cx) * full > 0]
kdf = KDTree(len(pool))
for k, i in enumerate(pool): kdf.insert(W[i], k)
kdf.balance()
new = {}; n1 = 0
for i in comp | neckv:
    p = W[i]
    if (p.x - cx) * full >= 0 or not (1.585 - off < p.z < Y1 - off): continue
    t = ang(p)
    w = ss((Y1 - (p.z + off)) / 0.02) * ss((t - T0) / 15.0) * ss((T1 - t) / 20.0)
    if i not in comp: w *= ss(1.0 - kds.find(p)[2] / NECK)
    if w <= 0: continue
    m = Vector((2 * cx - p.x, p.y, p.z))
    nb = kdf.find_n(m, 3)
    acc = {}; tot = 0.0
    for _co, k, d in nb:
        iw = 1.0 / max(d, 1e-4); tot += iw
        for n, x in weights(pool[k]).items(): acc[mir[n]] = acc.get(mir[n], 0.0) + iw * x
    mw_ = {n: x / tot for n, x in acc.items()}
    own = weights(i)
    names = set(own) | set(mw_)
    new[i] = {n: (1 - w) * own.get(n, 0.0) + w * mw_.get(n, 0.0) for n in names}; n1 += 1
# step 2: clavicle fade on the head shell, both sides
n2 = 0; clav0 = 0.0; clav1 = 0.0
for i in comp:
    wt = new.get(i) or weights(i)
    z = W[i].z + off
    k = 1.0 - ss((z - 1.67) / 0.03)
    c = {n: x for n, x in wt.items() if 'Clavicle' in n}
    if not c or k >= 1.0:
        if i in new: new[i] = wt
        continue
    moved = sum(c.values()) * (1 - k); clav0 += sum(c.values())
    for n in c: wt[n] *= k
    wt['Bip01 Head'] = wt.get('Bip01 Head', 0.0) + moved; clav1 += sum(wt[n] for n in c)
    new[i] = wt; n2 += 1
# step 3: the jaw follows the head (r10 viewer check: in Standing the head pitches 8.6 deg against an asymmetric neck/clavicle pose
# and the neck/clavicle share of the jaw bent the two sides differently, head-local mirror asymmetry p95 14-18 mm): on the head
# shell, Neck and Clavicle weights fade from the neck seam (kept within SEAM_KEEP) to 0 at SEAM_KEEP + SEAM_FADE above it, the
# removed weight going to Bip01 Head; the neck bend then lives in the body neck and the shell's lowest strip
SEAM_KEEP, SEAM_FADE = 0.005, 0.02
n3 = 0
for i in comp:
    d = kds.find(W[i])[2]
    k = 1.0 - ss((d - SEAM_KEEP) / SEAM_FADE)
    if k >= 1.0: continue
    wt = new.get(i) or weights(i)
    c = {n: x for n, x in wt.items() if 'Clavicle' in n or n == 'Bip01 Neck'}
    if not c: continue
    moved = sum(c.values()) * (1 - k)
    for n in c: wt[n] *= k
    wt['Bip01 Head'] = wt.get('Bip01 Head', 0.0) + moved
    new[i] = wt; n3 += 1
for i, wt in new.items():
    s = sum(wt.values())
    for n, x in wt.items():
        g = ob.vertex_groups[n]
        if x / s > 1e-4: g.add([i], x / s, 'REPLACE')
        else: g.remove([i])
    for g in list(me.vertices[i].groups):
        if gname[g.group] not in wt: ob.vertex_groups[gname[g.group]].remove([i])
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('JAWWEIGHTS jaw to head', n3, 'shell vertices; mirrored', n1, 'narrow-side vertices; clavicle faded on', n2, 'shell vertices (sum', round(clav0, 2), '->',
      round(clav1, 2), '); bone mirror sample', {k: mir[k] for k in list(mir)[:0]} or
      {k: v for k, v in mir.items() if k != v and ('Clavicle' in k or k.startswith('Bone0') or k.startswith('Bone1'))})
