"""Raw Meshy parts -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.9297, as PEASANTF8).
Every shell is bisected at x = 0 and its +x half mirrored (the -x half has the open eye socket and the lip notch). Arms: the sleeve shell is
pulled in along the sleeve axis so the cuff ends at MM9's wrist (MM9 arm 0.458 m from the shoulder). Hands: posed MPFB (female), stub into
the cuff. Ears: procedural elf ears (Meshy left 1 cm stubs under the scarf). Legs: Meshy's +x leg and shoe moved onto MM9's foot, cut below
the knee, mirrored. Eyeball cups and the ear stubs dropped (the shell carries the painted eyes).
Args: <raw npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
RAW, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
Z0 = -0.9297; X0 = float(os.environ.get('X0', '0.008'))
D = np.load(RAW); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection


def mesh(name, c, t):
    u, inv = np.unique(t.ravel(), return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[u].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    return o


def C(*cs): return tri[np.isin(comp[tri[:, 0]], cs)]


def mirror_mid(o, keep_positive=True):
    """bisect at x = 0, keep one half, add its mirror image with reversed winding, weld the midline (numpy, no bmesh.ops.mirror)"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=not keep_positive, clear_inner=keep_positive, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]); t = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
    c[np.abs(c[:, 0]) < 1e-4, 0] = 0
    n = len(c); mid = np.abs(c[:, 0]) < 1e-9
    idx = np.arange(n) + n; idx[mid] = np.where(mid)[0]
    c2 = np.vstack([c, c * [-1, 1, 1]]); t2 = np.vstack([t, idx[t][:, ::-1]])
    used, inv = np.unique(t2.ravel(), return_inverse=True)
    me.clear_geometry(); me.from_pydata(c2[used].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()


def pair(o):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces); ret = bmesh.ops.duplicate(bm, geom=g)
    for e in ret['geom']:
        if isinstance(e, bmesh.types.BMVert): e.co.x = -e.co.x
    bmesh.ops.reverse_faces(bm, faces=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]); bm.to_mesh(me); bm.free()


def verts(o): return np.array([v.co[:] for v in o.data.vertices])


def setv(o, P):
    for v, p in zip(o.data.vertices, P): v.co = Vector(p)
    o.data.update()


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


parts = {}
parts['head'] = mesh('head', co, C(0)); mirror_mid(parts['head'])
# the small human ear of the Meshy head is pressed into the skull: the elf ear below takes its place
EC = np.array([float(x) for x in os.environ.get('EAR_C', '0.074,-0.081,1.590').split(',')]) + [0, 0, Z0]
def flatten_ears(o):
    me = o.data; me.calc_loop_triangles(); P = verts(o); t = np.array([lt.vertices[:] for lt in me.loop_triangles]); n = len(P)
    e = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    deg = np.zeros(n); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1); S = P.copy()
    for _ in range(60):
        acc = np.zeros_like(S); np.add.at(acc, e[:, 0], S[e[:, 1]]); np.add.at(acc, e[:, 1], S[e[:, 0]])
        S = 0.5 * S + 0.5 * acc / np.maximum(deg, 1)[:, None]
    q = P * [1, 1, 1]; q[:, 0] = np.abs(q[:, 0])
    r = np.linalg.norm(q - EC, axis=1); w = 1 - ss(r, 0.022, 0.040)
    P = P + (S - P) * (0.85 * w)[:, None]
    print('EARS flattened', int((w > 0.5).sum()), 'verts')
    setv(o, P)
flatten_ears(parts['head'])
parts['scarf'] = mesh('scarf', co, C(6)); mirror_mid(parts['scarf'])
parts['dress'] = mesh('dress', co, C(1)); mirror_mid(parts['dress'])
parts['cuffs'] = mesh('cuffs', co, tri[(comp[tri[:, 0]] == 10)]); pair(parts['cuffs'])
parts['band'] = mesh('band', co, C(9)); mirror_mid(parts['band'])
parts['skirt'] = mesh('skirt', co, C(2)); mirror_mid(parts['skirt'])
# ---- legs: the +x leg with its shoe, onto MM9's foot (x 0.091), cut below the knee
LEGX = float(os.environ.get('LEGX', '0.091'))
lg = mesh('legs', co, C(3)); P = verts(lg)
P[:, 0] += LEGX - 0.5 * (P[P[:, 2] < Z0 + 0.08, 0].min() + P[P[:, 2] < Z0 + 0.08, 0].max())
P[:, 1] += float(os.environ.get('LEGY', '0.045'))       # ankle onto MM9's Foot joint (y 0.051)
setv(lg, P)
bm = bmesh.new(); bm.from_mesh(lg.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, Z0 + float(os.environ.get('LEGTOP', '0.42'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(lg.data); bm.free(); pair(lg); parts['legs'] = lg
# ---- sleeve axis (on dress + cuffs, +x side)
def joined_arrays(*os_):
    Cs, Ts, b = [], [], 0
    for o in os_:
        me = o.data; me.calc_loop_triangles(); c = verts(o); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
        Cs.append(c); Ts.append(t + b); b += len(c)
    return np.vstack(Cs), np.vstack(Ts)
rc, rt = joined_arrays(parts['dress'], parts['cuffs'])
d = np.array([.80, -0.08, -.60]); d /= np.linalg.norm(d); p = np.array([.24, -.040, 1.308 + Z0]); line = []
for i in range(24):
    l = nearest_loop(section(rc, rt, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > .07: break
    line.append(l['c']); d2 = l['c'] - (line[-2] if len(line) > 1 else p); p = l['c'] + d * .02
line = np.array(line)
ax = line[-3] - line[1]; ax /= np.linalg.norm(ax)
print('SLEEVE line', len(line), line[0].round(3), line[-1].round(3), 'axis', ax.round(3))
MM9_SH = np.array([0.163, 0.033, 1.347 + Z0]); MM9_ARM = 0.458
sh = line[0] + ax * ((MM9_SH[0] - line[0][0]) / ax[0])
cuffP = verts(parts['cuffs']); cuffP = cuffP[cuffP[:, 0] > 0]
tend = float(((cuffP - sh) @ ax).max())
S_ARM = (MM9_ARM + float(os.environ.get('CUFFOVER', '0.0'))) / tend
print('SHOULDER on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'cuff end t', round(tend, 3), 'arm scale', round(S_ARM, 3))
def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K
MM9_DIR = np.array([0.379, -0.026, -0.258]); MM9_DIR /= np.linalg.norm(MM9_DIR)
print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))
def pull(o):
    """the sleeve beyond the shoulder cap: scaled along the axis to MM9's length and turned onto MM9's arm direction"""
    P = verts(o)
    for sgn in (1, -1):
        a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
        t = (P - s0) @ a; side = np.where(P[:, 0] * sgn > 0)[0]
        k = ss(t, -0.02, 0.10)
        for i in side:
            if k[i] <= 0: continue
            q = P[i] + a * (max(t[i], 0) * (S_ARM - 1) * k[i])
            P[i] = s0 + rodr(a, m, k[i]) @ (q - s0)
    setv(o, P)
pull(parts['dress']); pull(parts['cuffs'])
ax = MM9_DIR.copy()
wr = sh + ax * MM9_ARM
print('WRIST', wr.round(3))
# ---- hands: posed MPFB, fingers along the arm axis, thumb forward, palm down
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd, t0 = [np.array(F[k]) for k in ('w', 'hd', 't')]
S = float(os.environ.get('HANDLEN', '0.175')) / F['L']
fd = ax.copy(); th = np.array([0, -1.0, 0]); th -= fd * (th @ fd); th /= np.linalg.norm(th)
A = np.c_[hd, t0, np.cross(hd, t0)]; nz = np.cross(fd, th); B = np.c_[fd, th, nz]
Rm = B @ A.T
print('HAND det', round(np.linalg.det(Rm), 4), 'scale', round(S, 4))
def tf0(p): return (np.asarray(p) - w0) @ Rm.T * S + wr
hq0 = tf0(hc); al = (hq0 - wr) @ fd; beh = hq0[al < -0.04]; sd = (wr - beh.mean(0)); sd /= np.linalg.norm(sd)
print('HAND stub axis vs sleeve deg', round(float(np.degrees(np.arccos(np.clip(sd @ fd, -1, 1)))), 1))
def tf(p):
    p = np.atleast_2d(tf0(p)); a = (p - wr) @ fd; k = np.clip((0.03 - a) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
    return np.array([wr + rodr(sd, fd, k[i]) @ (p[i] - wr) for i in range(len(p))])
hq = tf(hc); al = (hq - wr) @ fd
# the forearm stub: cut 6 cm behind the wrist and held inside a 2.6 cm radius round the axis, so it never shows through the cuff wall
STUB = float(os.environ.get('STUB', '0.06')); RMAX = float(os.environ.get('STUBR', '0.026'))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1); k = (al < -0.005) & (r > RMAX)
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * RMAX
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()))
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- ears: a cupped leaf with a rim, root inside the head at the Meshy stub, tip out, up and a little back
ER = np.array([float(x) for x in os.environ.get('EAR_ROOT', '0.064,-0.080,1.575').split(',')]) + [0, 0, Z0]
eu = np.array([float(x) for x in os.environ.get('EAR_DIR', '0.75,0.25,0.62').split(',')]); eu /= np.linalg.norm(eu)
en = np.array([1.0, -0.55, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)     # front face: out and forward, as a real ear
ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
EL = float(os.environ.get('EAR_LEN', '0.085')); EW = float(os.environ.get('EAR_W', '0.046'))
NU, NV = 12, 7
uu = np.linspace(0, 1, NU); vv = np.linspace(-1, 1, NV)
V = []; T = []
for side, sgn in (('front', 1), ('back', -1)):
    for i, u in enumerate(uu):
        wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)         # widest at a third, a point at the tip
        th_ = 0.0055 * (1 - u) ** 0.7 + 0.0012
        for j, v in enumerate(vv):
            cup = 0.006 * (1 - v * v) * np.sin(np.pi * min(u * 1.1, 1)) if sgn > 0 else 0.0     # the bowl on the front
            rim = 0.002 * np.exp(-((abs(v) - 1) / 0.3) ** 2) * (1 - u) if sgn > 0 else 0.0     # the rolled edge
            off = sgn * th_ * np.sqrt(max(1 - v * v, 0.0)) - cup + rim
            p = ER + eu * (u * EL) + ev * (v * wid * 0.5) + en * off
            V.append(p)
nf = NU * NV
for s in (0, 1):
    for i in range(NU - 1):
        for j in range(NV - 1):
            a = s * nf + i * NV + j; b = a + 1; c_ = a + NV; d_ = c_ + 1
            T += [[a, b, d_], [a, d_, c_]] if s == 0 else [[a, d_, b], [a, c_, d_]]
# stitch the two sides along the edges v = -1 and v = +1, and close the tip
for i in range(NU - 1):
    for j in (0, NV - 1):
        a, c_ = i * NV + j, (i + 1) * NV + j; b, d_ = nf + a, nf + c_
        T += [[a, c_, d_], [a, d_, b]] if j == 0 else [[a, d_, c_], [a, b, d_]]
V = np.array(V); V[(NU - 1) * NV:nf] = V[(NU - 1) * NV:nf].mean(0); V[nf + (NU - 1) * NV:] = V[(NU - 1) * NV:nf].mean(0)
ear = mesh('ears', V, np.array(T))
bm = bmesh.new(); bm.from_mesh(ear.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ear.data); bm.free()
pair(ear); parts['ears'] = ear
# ---- holes: the cuff's 11-edge gap, the open shoe soles and the cut leg tops
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['cuffs'], 12); fill(parts['legs'], 100)
# ---- reduce outside the head (symmetric collapse; the head keeps Meshy's density), before the lining and the weights
BUDGET = dict(dress=1800, skirt=1400, legs=640, scarf=950, cuffs=520, band=260)
def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
for nm, b in BUDGET.items():
    o_ = parts[nm]; t0_ = tris(o_)
    if t0_ <= b * 1.02: continue
    for x in bpy.data.objects: x.select_set(x is o_)
    bpy.context.view_layer.objects.active = o_
    md = o_.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = b / t0_; md.use_symmetry = True; md.symmetry_axis = 'X'; md.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='d'); print('REDUCE', nm, t0_, '->', tris(o_))
# ---- skirt lining: an inner copy 4 mm in, reversed, one rim strip along the hem and the apron's lower edge (a corpse is seen from the feet)
def lining(src, name, depth=0.004, top=Z0 + 1.03):
    me = src.data; bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]); n = np.array([v.normal[:] for v in bm.verts])
    t = np.array([[v.index for v in f.verts] for f in bm.faces])
    bnd = [(e.verts[0].index, e.verts[1].index, e.link_faces[0]) for e in bm.edges if e.is_boundary]
    rim = []
    for a, b, f in bnd:
        if min(c[a, 2], c[b, 2]) > top: continue
        vs = [v.index for v in f.verts]; i = vs.index(a)
        if vs[(i + 1) % 3] != b: a, b = b, a          # a -> b runs along the face's winding
        rim.append((a, b))
    bm.free(); N = len(c)
    ci = c - n * depth
    T = [list(f[::-1] + N) for f in t]
    for a, b in rim: T += [[b, a, a + N], [b, a + N, b + N]]
    o = mesh(name, np.vstack([c, ci]), np.array(T))
    print('LINING', name, len(t), 'faces + rim', 2 * len(rim))
    return o
lin = lining(parts['skirt'], 'lining')
parts['lining'] = lin
# ---- normals outward on closed parts; open shells keep Meshy's winding
for k in ('legs', 'hands'):
    bm = bmesh.new(); bm.from_mesh(parts[k].data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(parts[k].data); bm.free()
for o_ in parts.values():
    for p_ in o_.data.polygons: p_.use_smooth = True
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    me = parts[nm].data; me.calc_loop_triangles()
    c = verts(parts[nm]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
    print('PART', nm, len(c), len(t))
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names), sh=sh, wr=wr, ax=ax, hj=json.dumps(hj2), hand_scale=S,
         hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], arm_scale=S_ARM)
print('SAVED', base, sum(len(t) for t in Tr))
