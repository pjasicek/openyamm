"""PeasantM4 trunk reshape on PeasantM8's master (positions only; topology, UVs, weights unchanged).
MM9's PeasantM4 mesh = PeasantM8's mesh with a fuller belly, waist, hips and thighs (same skeleton, same binds). The
offset field is measured between the two MM9 meshes (M4 surface along PM8's normal), smoothed, and applied to our
vertices along our normals, weighted by the trunk/thigh bone share, then smoothed over the mesh with head, arms and
lower legs pinned.
Usage: blender -b --python reshape_m4.py -- in.blend out.blend pm8mm9.npz m4mm9.npz report.json [gain]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

def kd(points):
    t = KDTree(len(points))
    for i, p in enumerate(points):
        t.insert(Vector(p), i)
    t.balance()
    return t
argv = sys.argv[sys.argv.index('--') + 1:]
src, dst, fa, fb, rep = argv[:5]
gain = float(argv[5]) if len(argv) > 5 else 1.0
A, B = np.load(fa), np.load(fb)

def surf(co, tris, n=4):
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    nrm = np.cross(b - a, c - a); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
    P, N = [], []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            u, v = i / n, j / n
            P.append(a + u * (b - a) + v * (c - a)); N.append(nrm)
    return np.concatenate(P), np.concatenate(N)

PA, NA = surf(A['co'], A['tris']); PB, _ = surf(B['co'], B['tris'])
# field on PM8's MM9 surface: signed distance of M4's surface along PM8's normal (nearest M4 sample)
tb = kd(PB)
j = np.array([tb.find(Vector(p))[1] for p in PA])
f = np.einsum('ij,ij->i', PB[j] - PA, NA)
# smooth over 5 cm, bounded memory (chunks)
ta = kd(PA)
fs = np.array([f[[r[1] for r in ta.find_range(Vector(p), 0.05)]].mean() for p in PA])

bpy.ops.wm.open_mainfile(filepath=src)
o = bpy.data.objects['Body']
me = o.data
co = np.array([v.co for v in me.vertices])
nrm = np.array([v.normal for v in me.vertices])
vg = {g.index: g.name for g in o.vertex_groups}
TRUNK = ('Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2', 'Bip01 Pelvis', 'Bip01 L Thigh', 'Bip01 R Thigh', 'Bip01')
w = np.zeros(len(co))
pin = np.zeros(len(co), bool)
for v in me.vertices:
    tot = 0.0; tr = 0.0
    for g in v.groups:
        n = vg[g.group]; tot += g.weight
        if n in TRUNK or (n.startswith('Bone') and 'Bip01' not in n):
            tr += g.weight
    w[v.index] = tr / tot if tot > 0 else 0.0
    dom = max(v.groups, key=lambda g: g.weight) if len(v.groups) else None
    dn = vg[dom.group] if dom else ''
    if any(k in dn for k in ('Head', 'Neck', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Calf', 'Foot', 'Toe')):
        pin[v.index] = True
# SPATIAL field (v3): every vertex at x moves by the Gaussian-weighted mean of the MM9 offset vectors (fs * normal)
# of the PM8 MM9 samples within 7 cm, so stacked layers (vest hem over the waistband) move together.
vec = fs[:, None] * NA
move = np.zeros_like(co)
for i, p in enumerate(co):
    if pin[i]:
        continue
    hits = ta.find_range(Vector(p), 0.07)
    if not hits:
        continue
    idx = np.array([h[1] for h in hits]); dist = np.array([h[2] for h in hits])
    g = np.exp(-0.5 * (dist / 0.03) ** 2)
    move[i] = (vec[idx] * g[:, None]).sum(0) / g.sum()
# height window: full from the knee (z -0.40) to the lower chest (z 0.35), fading 10 cm beyond
z = co[:, 2]
hw = np.clip((z + 0.50) / 0.10, 0, 1) * np.clip((0.45 - z) / 0.10, 0, 1)
move *= hw[:, None] * gain
move[pin] = 0.0
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
for _ in range(10):
    nm = move.copy()
    for i, nb in enumerate(nbrs):
        if pin[i] or not nb:
            continue
        nm[i] = 0.5 * move[i] + 0.5 * move[nb].mean(0)
    move = nm
d = np.einsum('ij,ij->i', move, nrm)
for v in me.vertices:
    v.co = Vector(co[v.index] + move[v.index])
me.update()
bpy.ops.wm.save_as_mainfile(filepath=dst)
np.save(dst.replace('.blend', '_move.npy'), np.concatenate([co, move], 1))
m = np.linalg.norm(move, axis=1)
r = {'field_p50_cm': float(np.percentile(f, 50) * 100), 'field_p90_cm': float(np.percentile(f, 90) * 100),
     'moved_vertices': int((m > 1e-4).sum()), 'move_max_cm': float(m.max() * 100), 'move_p90_moved_cm': float(np.percentile(m[m > 1e-4], 90) * 100),
     'inward_min_cm': float(d.min() * 100), 'gain': gain}
json.dump(r, open(rep, 'w'), indent=1); print('RESHAPE', r)
