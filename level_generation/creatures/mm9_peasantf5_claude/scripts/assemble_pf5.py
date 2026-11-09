"""Raw Meshy parts -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.9297, as PEASANTF5).
From PeasantF8's assemble_pf.py. Every shell is bisected at x = 0 and its +x half mirrored (the -x eye is malformed). Arms: Meshy's bare-arm
shell (from inside the puffed sleeve to the wrist) and the puffed sleeve are pulled along the arm axis so the wrist sits at MM9's arm length
(0.459 m from the shoulder) and turned onto MM9's arm direction. Meshy's hand and the arm's closing cap are dropped; posed MPFB (female) hands
with a short stub into the forearm; a procedural bracelet band covers the joint (MM9's skin has a bracelet there). Legs: Meshy's +x leg and shoe
moved onto MM9's foot, cut below the knee, mirrored. Eyeballs and mouth inserts dropped (the head shell carries the painted eyes).
Args: <raw npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
RAW, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
Z0 = -0.9297; X0 = float(os.environ.get('X0', '0.009'))
D = np.load(RAW); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
# raw components (step1_clean.py order, scaled to 1.806 m)
CMP = dict(head=(0, 12), dress=1, skirt=4, arm=6, leg=8, shoe=10, coif=9, buckle=16, orn=(18, 20))


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


def arrays(o):
    me = o.data; me.calc_loop_triangles(); return verts(o), np.array([lt.vertices[:] for lt in me.loop_triangles])


parts = {}
for nm in ('head', 'coif', 'dress', 'skirt'):
    cc_ = CMP[nm] if isinstance(CMP[nm], tuple) else (CMP[nm],)
    parts[nm] = mesh(nm, co, C(*cc_)); mirror_mid(parts[nm])      # head: the +x eyeball kept (and mirrored), it fills the socket
orn = mesh('ornaments', co, C(*CMP['orn'])); pair(orn)
bk = mesh('buckle', co, C(CMP['buckle'])); mirror_mid(bk)
# ---- legs: the +x leg with its shoe, onto MM9's foot (x 0.091), cut below the knee
LEGX = float(os.environ.get('LEGX', '0.091'))
lg = mesh('legs', co, C(CMP['leg'], CMP['shoe'])); P = verts(lg)
P[:, 0] += LEGX - 0.5 * (P[P[:, 2] < Z0 + 0.08, 0].min() + P[P[:, 2] < Z0 + 0.08, 0].max())
P[:, 1] += float(os.environ.get('LEGY', '0.045'))
setv(lg, P)
bm = bmesh.new(); bm.from_mesh(lg.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, Z0 + float(os.environ.get('LEGTOP', '0.42'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(lg.data); bm.free(); pair(lg); parts['legs'] = lg
# ---- the bare arm (+x shell): axis from ring centres
arm = mesh('arms', co, C(CMP['arm']))
ac, at = arrays(arm)
m0 = ac.mean(0); _, _, vt = np.linalg.svd(ac - m0); ax0 = vt[0] * np.sign(vt[0][0])
tt = (ac - m0) @ ax0; cs = []
for tv in np.linspace(tt.min() + 0.05, tt.max() - 0.03, 10):
    l = nearest_loop(section(ac, at, m0 + ax0 * tv, ax0), m0 + ax0 * tv)
    if l is not None: cs.append(l['c'])
cs = np.array(cs); mc = cs.mean(0); _, _, vt = np.linalg.svd(cs - mc); ax = vt[0] * np.sign(vt[0][0])
MM9_SH = np.array([0.163, 0.033, 1.347 + Z0]); MM9_ARM = 0.459
sh = mc + ax * ((MM9_SH[0] - mc[0]) / ax[0])
tend = float(((ac - sh) @ ax).max())
CAP = float(os.environ.get('CAP', '0.008'))         # the closing cap of Meshy's arm, cut off (the hand replaces it)
S_ARM = MM9_ARM / (tend - CAP)
print('ARM axis', ax.round(3), 'shoulder on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'arm end t', round(tend, 3), 'arm scale', round(S_ARM, 3))


def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


MM9_DIR = np.array([0.379, -0.026, -0.258]); MM9_DIR /= np.linalg.norm(MM9_DIR)
print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))
# cut the cap (the arm's last CAP metres) before the pull
bm = bmesh.new(); bm.from_mesh(arm.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=tuple(sh + ax * (tend - CAP)), plane_no=tuple(ax), clear_outer=True, dist=1e-5)
bm.to_mesh(arm.data); bm.free()
pair(arm); parts['arms'] = arm


def pull(o, both=True):
    """beyond the shoulder cap: scaled along the axis to MM9's length and turned onto MM9's arm direction"""
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


pull(parts['dress']); pull(parts['arms'])
ax = MM9_DIR.copy()
wr = sh + ax * MM9_ARM
P = verts(parts['arms']); pa = P[P[:, 0] > 0]; tw = (pa - sh) @ ax
ring = pa[tw > MM9_ARM - 0.006]; rr = np.linalg.norm(ring - sh - ((ring - sh) @ ax)[:, None] * ax, axis=1)
print('WRIST', wr.round(3), 'arm end ring radius', round(float(rr.mean()), 4), round(float(rr.min()), 4), round(float(rr.max()), 4))
# ---- hands: posed MPFB, fingers along the arm axis, thumb forward, palm down
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd, t0 = [np.array(F[k]) for k in ('w', 'hd', 't')]
S = float(os.environ.get('HANDLEN', '0.170')) / F['L']
fd = ax.copy(); th = np.array([0, -1.0, 0]); th -= fd * (th @ fd); th /= np.linalg.norm(th)
A = np.c_[hd, t0, np.cross(hd, t0)]; nz = np.cross(fd, th); B = np.c_[fd, th, nz]
Rm = B @ A.T
print('HAND det', round(np.linalg.det(Rm), 4), 'scale', round(S, 4))
def tf0(p): return (np.asarray(p) - w0) @ Rm.T * S + wr
hq0 = tf0(hc); al = (hq0 - wr) @ fd; beh = hq0[al < -0.04]; sd = (wr - beh.mean(0)); sd /= np.linalg.norm(sd)
print('HAND stub axis vs arm deg', round(float(np.degrees(np.arccos(np.clip(sd @ fd, -1, 1)))), 1))
def tf(p):
    p = np.atleast_2d(tf0(p)); a = (p - wr) @ fd; k = np.clip((0.03 - a) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
    return np.array([wr + rodr(sd, fd, k[i]) @ (p[i] - wr) for i in range(len(p))])
hq = tf(hc); al = (hq - wr) @ fd
# the stub: cut STUB behind the wrist and held inside the forearm (radius RMAX round the axis), so it never shows through the arm skin
STUB = float(os.environ.get('STUB', '0.035')); RMAX = float(os.environ.get('STUBR', str(max(float(rr.min()) - 0.003, 0.012))))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1)
kk = np.clip(-al / 0.012, 0, 1); lim = RMAX + (r - RMAX) * (1 - kk); k = r > lim
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * lim[k, None]
rw = r[(al > -0.004) & (al < 0.004)]
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()), 'stub radius', round(RMAX, 4), 'hand radius at wrist', round(float(rw.max()), 4) if len(rw) else None)
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- bracelets: a rounded band round the wrist, over the arm/hand joint (MM9 paints a copper bracelet there), fitted per angle to the larger
# of the arm's end and the hand's wrist within the band, plus a small gap
BR_W = float(os.environ.get('BR_W', '0.011')); BR_T = float(os.environ.get('BR_T', '0.003'))
BR_C = float(os.environ.get('BR_C', '-0.003')); BR_GAP = float(os.environ.get('BR_GAP', '0.0012'))
u0 = np.cross(fd, [0, 0, 1.0]); u0 /= np.linalg.norm(u0); v0 = np.cross(fd, u0)
NA, NS = 24, 8
Pa_ = verts(parts['arms']); Pa_ = Pa_[Pa_[:, 0] > 0]
src_ = np.vstack([Pa_, hq]); a_ = (src_ - wr) @ fd
band_ = src_[np.abs(a_ - BR_C) < 0.5 * BR_W + 0.004]; rel_ = band_ - wr - ((band_ - wr) @ fd)[:, None] * fd
phi_ = np.arctan2(rel_ @ v0, rel_ @ u0); rad_ = np.linalg.norm(rel_, axis=1)
prof = np.zeros(NA)
for i in range(NA):
    ph = 2 * np.pi * i / NA; d_ = np.abs((phi_ - ph + np.pi) % (2 * np.pi) - np.pi)
    sel_ = d_ < 2 * np.pi / NA * 1.2
    prof[i] = rad_[sel_].max() if sel_.any() else rad_.max()
for _ in range(2): prof = 0.5 * prof + 0.25 * (np.roll(prof, 1) + np.roll(prof, -1))
prof += BR_GAP
V = []
for i in range(NA):
    ph = 2 * np.pi * i / NA; dr = u0 * np.cos(ph) + v0 * np.sin(ph)
    for j in range(NS):
        ps = 2 * np.pi * j / NS
        V.append(wr + fd * (BR_C + 0.5 * BR_W * np.cos(ps)) + dr * (prof[i] + BR_T * 0.5 * (1 + np.sin(ps))))
T = []
for i in range(NA):
    for j in range(NS):
        a = i * NS + j; b = i * NS + (j + 1) % NS; c_ = ((i + 1) % NA) * NS + j; d_ = ((i + 1) % NA) * NS + (j + 1) % NS
        T += [[a, c_, d_], [a, d_, b]]
br = mesh('bracelets', np.array(V), np.array(T))
bm = bmesh.new(); bm.from_mesh(br.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(br.data); bm.free()
pair(br); parts['bracelets'] = br
BR_R = float(prof.mean())
print('BRACELET radius', round(BR_R, 4), 'width', BR_W)
parts['ornaments'] = orn; parts['buckle'] = bk
# ---- holes: the cut leg tops and shoe soles, the cut arm ends stay open inside the bracelet
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['legs'], 100)
# ---- reduce outside the head (symmetric collapse; the head keeps Meshy's density), before the lining and the weights
BUDGET = dict(dress=2000, legs=640, arms=900, coif=900, skirt=1400)
def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
for nm, b in BUDGET.items():
    o_ = parts[nm]; t0_ = tris(o_)
    if t0_ <= b * 1.02: print('KEEP', nm, t0_); continue
    for x in bpy.data.objects: x.select_set(x is o_)
    bpy.context.view_layer.objects.active = o_
    md = o_.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = b / t0_; md.use_symmetry = True; md.symmetry_axis = 'X'; md.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='d'); print('REDUCE', nm, t0_, '->', tris(o_))
# ---- skirt lining: an inner copy 4 mm in, reversed, one rim strip along the hem (a corpse is seen from the feet)
def lining(src, name, depth=0.004, top=Z0 + 1.03):
    me = src.data; bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]); n = np.array([v.normal[:] for v in bm.verts])
    t = np.array([[v.index for v in f.verts] for f in bm.faces])
    bnd = [(e.verts[0].index, e.verts[1].index, e.link_faces[0]) for e in bm.edges if e.is_boundary]
    rim = []
    for a, b, f in bnd:
        if min(c[a, 2], c[b, 2]) > top: continue
        vs = [v.index for v in f.verts]; i = vs.index(a)
        if vs[(i + 1) % 3] != b: a, b = b, a
        rim.append((a, b))
    bm.free(); N = len(c)
    ci = c - n * depth
    T = [list(f[::-1] + N) for f in t]
    for a, b in rim: T += [[b, a, a + N], [b, a + N, b + N]]
    o = mesh(name, np.vstack([c, ci]), np.array(T))
    print('LINING', name, len(t), 'faces + rim', 2 * len(rim))
    return o
if os.environ.get('LINING', '1') == '1':
    parts['lining'] = lining(parts['skirt'], 'lining')
for k in ('legs', 'hands'):
    bm = bmesh.new(); bm.from_mesh(parts[k].data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(parts[k].data); bm.free()
for o_ in parts.values():
    for p_ in o_.data.polygons: p_.use_smooth = True
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    c, t = arrays(parts[nm])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
    print('PART', nm, len(c), len(t))
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names), sh=sh, wr=wr, ax=ax, hj=json.dumps(hj2), hand_scale=S,
         hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], arm_scale=S_ARM)
print('SAVED', base, sum(len(t) for t in Tr))
