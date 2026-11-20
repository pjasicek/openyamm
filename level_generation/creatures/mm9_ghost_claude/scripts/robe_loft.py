"""One clean robe from Meshy's two overlapping sheets (front shell + inner skirt): a see-through robe may not hide a second layer, an inner rim or a seam.
Rays from a curved axis to the outermost sheet give r(theta, s) on a fine grid; that grid is
- the coarse tube mesh (Robe, outer faces, mirror-symmetric, regular rings: Nt x Ns quads, belt ridge in the top rings),
- the hem mask work/robe_mask.npz (what is sheet and what is air: the tatters are alpha, not geometry).
Attribute robe_st (corner, FLOAT2): theta/2pi, s, for the alpha bake and the chain weights.
Args: <upper blend> <sheets npz> <out blend> <mask npz>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
UP, NPZ, OUT, MASK = a
Nt, Ns = 40, 20                    # coarse tube
GT, GS = 361, 512                  # half-round fine grid
TARGET_HEM = -0.734                # MM9 hem height
BELT = 0.045                       # belt height (below the top ring)
RIDGE = 0.006                      # belt stands off the cloth
d = np.load(NPZ)
W, tris, comp = d['co'], d['tris'], d['comp']
main, head = int(d['main']), int(d['head'])
zcut = float(d['zcut'])
tcomp = comp[tris[:, 0]]
sizes = np.bincount(comp)
inner = np.argsort(sizes)[::-1][2]          # the skirt sheet
cen = W[tris].mean(1)
use = np.isin(tcomp, [main, inner]) & (cen[:, 2] < zcut + 0.02) & (cen[:, 0] > -0.02) & (cen[:, 0] < 0.2 + 0.5 * np.maximum(zcut - cen[:, 2], 0))
# the strap from the hand to the hem lies at x < 0: only the x > 0 half is read and mirrored
bvh = BVHTree.FromPolygons([Vector(c.tolist()) for c in W], tris[use].tolist())
print('SHEET faces', use.sum(), 'inner comp', inner, sizes[inner])
Wu = W[np.unique(tris[use])]
hem = Wu[Wu[:, 2] < Wu[:, 2].min() + 0.12]
y_w = float(0.5 * (W[(np.abs(W[:, 2] - zcut) < 0.02) & (np.abs(W[:, 0]) < 0.2), 1].min() + W[(np.abs(W[:, 2] - zcut) < 0.02) & (np.abs(W[:, 0]) < 0.2), 1].max()))
P0 = np.array([0, y_w, zcut]); H = np.array([0, float(0.5 * (hem[:, 1].min() + hem[:, 1].max())), float(Wu[:, 2].min()) - 0.01])
P1 = np.array([0, y_w, 0.5 * (zcut + H[2])])
print('AXIS', P0, P1, H)


def axis(s):
    s = np.asarray(s)[..., None]
    return (1 - s) ** 2 * P0 + 2 * s * (1 - s) * P1 + s ** 2 * H


def tangent(s):
    s = np.asarray(s)[..., None]
    t = 2 * (1 - s) * (P1 - P0) + 2 * s * (H - P1)
    return t / np.linalg.norm(t, axis=-1, keepdims=True)


def dirs(s, th):
    """outward ray in the ring plane; th 0 = front (-y), pi/2 = +x, pi = back"""
    t = tangent(s)
    x = np.array([1.0, 0, 0])
    f = np.cross(t, x)                           # forward-ish in the ring plane
    f = f / np.linalg.norm(f)
    if f[1] > 0:
        f = -f
    return np.cos(th) * f + np.sin(th) * x


ss = np.linspace(0, 1, GS)
th = np.linspace(0, np.pi, GT)
R = np.full((GS, GT), np.nan)
for i, s in enumerate(ss):
    c = axis(s)
    for j, t in enumerate(th):
        dv = dirs(s, t)
        hit = bvh.ray_cast(Vector((c + dv * 1.2).tolist()), Vector((-dv).tolist()), 1.2)
        if hit[0] is not None:
            R[i, j] = 1.2 - hit[3]
mask = np.isfinite(R)
print('MASK cover', mask.mean(), 'first rows', mask[:3].mean(1))
# fill the air: across each row first (between the tatters), then rows past the last sheet keep the last radius
F = R.copy()
for j in range(GT):
    col = F[:, j]; good = np.where(np.isfinite(col))[0]
    last_ = good.max()
    g0 = good[max(len(good) - 30, 0)]
    sl = (col[last_] - col[g0]) / max(last_ - g0, 1)     # past the tatter's tip the meridian goes on straight
    for i in range(GS):
        if np.isnan(col[i]):
            if i > last_:
                col[i] = max(col[last_] + sl * (i - last_), 0.03)
            else:
                nxt = good[good > i].min(); prv = good[good < i].max()
                col[i] = col[prv] + (col[nxt] - col[prv]) * (i - prv) / (nxt - prv)
# hem envelope: how far the sheet reaches at each angle, dilated over the tatters' width
last = np.array([np.where(mask[:, j])[0].max() if mask[:, j].any() else 0 for j in range(GT)]) / (GS - 1)
wid = 28
env = np.array([last[max(0, j - wid):j + wid + 1].max() for j in range(GT)])
kern = np.exp(-0.5 * (np.arange(-30, 31) / 12.0) ** 2); kern /= kern.sum()
env = np.convolve(np.pad(env, 30, mode='reflect'), kern, 'same')[30:-30]
env = np.minimum(env + 0.012, 1.0)


def blur(A, st, sa):
    k1 = np.exp(-0.5 * (np.arange(-int(3 * st), int(3 * st) + 1) / st) ** 2); k1 /= k1.sum()
    k2 = np.exp(-0.5 * (np.arange(-int(3 * sa), int(3 * sa) + 1) / sa) ** 2); k2 /= k2.sum()
    p = np.pad(A, ((0, 0), (len(k1), len(k1))), mode='reflect')
    p = np.apply_along_axis(lambda m: np.convolve(m, k1, 'same'), 1, p)[:, len(k1):-len(k1)]
    p = np.pad(p, ((len(k2), len(k2)), (0, 0)), mode='edge')
    return np.apply_along_axis(lambda m: np.convolve(m, k2, 'same'), 0, p)[len(k2):-len(k2)]


Fs = blur(F, 7.0, 9.0)
np.savez(MASK, mask=mask, R=Fs, P0=P0, P1=P1, H=H, env=env)
# the waist rings take the jacket's own radius, so jacket and robe meet with no step
bpy.ops.wm.open_mainfile(filepath=UP)
_up = bpy.data.objects['Upper']
_mw = _up.matrix_world
_vU = [Vector((_mw @ v.co)[:]) for v in _up.data.vertices]
_bvhU = BVHTree.FromPolygons(_vU, [list(p.vertices) for p in _up.data.polygons if abs(_vU[p.vertices[0]].x) < 0.19 and abs(_vU[p.vertices[0]].z - zcut) < 0.05])
LIFT = 0.012
rU = np.zeros(GT)
_c = axis(0.0) + np.array([0, 0, LIFT])
for j, t in enumerate(th):
    dv = dirs(0.0, t)
    hit = _bvhU.ray_cast(Vector((_c + dv * 0.5).tolist()), Vector((-dv).tolist()), 0.5)
    rU[j] = 0.5 - hit[3] if hit[0] is not None else np.nan
rU = np.interp(np.arange(GT), np.where(np.isfinite(rU))[0], rU[np.isfinite(rU)])
rU = np.convolve(np.pad(rU, 12, mode='reflect'), np.ones(9) / 9, 'same')[12:-12]
print('WAIST radius', rU.min(), rU.max(), 'sheet', Fs[0].min(), Fs[0].max())
# coarse tube, s rings: belt ridge rings first
beltS = BELT / np.linalg.norm(H - P0)
rings = list(np.array([0.0, 0.25, 0.75, 1.0]) * beltS) + list(np.linspace(beltS, 1, Ns - 2)[1:])
rings[3] += 1e-3
scale = (0.083 - TARGET_HEM) / (0.083 - H[2])
print('ROBE scale', scale, 'rings', len(rings))
verts = []; st = []
for s_ring in rings:
    for k in range(Nt):
        t = 2 * math.pi * k / Nt                # 0 front, pi/2 +x, pi back, 3pi/2 -x
        tt = t if t <= math.pi else 2 * math.pi - t
        fi = tt / math.pi * (GT - 1)
        i0 = int(fi); i1 = min(i0 + 1, GT - 1); fr = fi - i0
        e = env[i0] * (1 - fr) + env[i1] * fr
        b_ = min(max((s_ring - 0.08) / 0.5, 0.0), 1.0); b_ = b_ * b_ * (3 - 2 * b_)
        s = s_ring * (1 + (e - 1) * b_)         # the rings follow the hem; the top rings stay planar
        fs = s * (GS - 1)
        j0 = int(fs); fq = fs - j0; j1 = min(j0 + 1, GS - 1)
        r = (Fs[j0, i0] * (1 - fr) + Fs[j0, i1] * fr) * (1 - fq) + (Fs[j1, i0] * (1 - fr) + Fs[j1, i1] * fr) * fq
        ru = rU[i0] * (1 - fr) + rU[i1] * fr
        w_ = min(max((s - beltS) / (1.6 * beltS), 0.0), 1.0); w_ = w_ * w_ * (3 - 2 * w_)
        r = ru * (1 - w_) + r * w_
        if 0.2 * beltS < s < 0.8 * beltS + 1e-6:
            r = r + RIDGE
        dv = dirs(s, t if t <= math.pi else t - 2 * math.pi)
        p = axis(s) + dv * r
        if s == 0.0:
            p = p + np.array([0, 0, LIFT])
        p = P0 + (p - P0) * np.array([1, scale, scale])
        verts.append(p); st.append((t / (2 * math.pi), s))
n = len(rings)
faces = []
for i in range(n - 1):
    for k in range(Nt):
        a0, b0 = i * Nt + k, i * Nt + (k + 1) % Nt
        a1, b1 = (i + 1) * Nt + k, (i + 1) * Nt + (k + 1) % Nt
        faces.append((a0, a1, b1, b0))
me = bpy.data.meshes.new('Robe')
me.from_pydata([v.tolist() for v in verts], [], faces)
me.update()
o = bpy.data.objects.new('Robe', me); bpy.context.scene.collection.objects.link(o)
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.loops.layers.float_vector.new('robe_st') if False else None
bm.to_mesh(me); bm.free()
# outward normals: tube faces point away from the axis
nv = np.array(verts)
c0 = me.polygons[Nt * 8].center
print('NORMAL check', (Vector(me.polygons[Nt * 8].normal)).dot(c0 - Vector(axis(rings[8]).tolist())))
vs = me.attributes.new('robe_s', 'FLOAT', 'POINT'); vt = me.attributes.new('robe_t', 'FLOAT', 'POINT')
vs.data.foreach_set('value', [q[1] for q in st]); vt.data.foreach_set('value', [q[0] for q in st])
for p in me.polygons:
    p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ROBE', len(me.vertices), len(me.polygons))
