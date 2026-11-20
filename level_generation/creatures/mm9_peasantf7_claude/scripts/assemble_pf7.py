"""PF7 (from assemble_pf1.py): segmented Meshy parts (seg_pf1.py) -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.9297).
Meshy fused head, hood, bodice and skirt into one shell: it is mirrored as one (bisected at the midline, the +x half kept), cut once along a
slanted neck plane so the head/body texture seam is a clean line, and split by the segmentation labels into head, scarf (the hood), dress
(blouse, bodice, short sleeves, lacing) and skirt (below the waist line). Eyes and lips stay on the head. Arms: Meshy's bare arms are
replaced by a posed, straightened MPFB female arm (upper-arm stub inside the short sleeve, forearm, five-finger hand) on Meshy's own arm axis,
MM9's length from the shoulder to the wrist. Legs: Meshy's +x leg and shoe on MM9's foot, cut below the knee, mirrored. Skirt lining 4 mm in.
Args: <seg npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
SEG, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
Z0 = -0.9297; X0 = float(os.environ.get('X0', '0.008'))
D = np.load(SEG); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']
HEADC, SKIRTC = 25, 26; HOODC = -99
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection


def mesh(name, c, t):
    u, inv = np.unique(t.ravel(), return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[u].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    return o


def C(*cs): return tri[np.isin(comp[tri[:, 0]], cs)]


def arrays(o):
    me = o.data; me.calc_loop_triangles()
    return np.array([v.co[:] for v in me.vertices]), np.array([lt.vertices[:] for lt in me.loop_triangles])


def mirror_mid(o, keep_positive=True):
    """bisect at x = 0, keep one half, add its mirror image with reversed winding, weld the midline (numpy)"""
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
# ---- the fused shell: mirror, neck cut, split by label
body = mesh('body', co, C(0, HEADC, SKIRTC)); mirror_mid(body)
NF = float(os.environ.get('NECK_F', '1.44')) + Z0; NB = float(os.environ.get('NECK_B', '1.48')) + Z0
pn = np.array([0, -(NB - NF), 0.16]); pn /= np.linalg.norm(pn); pc = np.array([0, -0.10, NF])
bm = bmesh.new(); bm.from_mesh(body.data)
sel = [f for f in bm.faces if np.hypot(f.calc_center_median().x, f.calc_center_median().y + 0.01) < 0.085 and NF - 0.06 < f.calc_center_median().z < NB + 0.06]
geo = list({v for f in sel for v in f.verts}) + list({e for f in sel for e in f.edges}) + sel
bmesh.ops.bisect_plane(bm, geom=geo, plane_co=pc.tolist(), plane_no=pn.tolist(), dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(body.data); bm.free()
bc, bt = arrays(body)
src = np.where(np.isin(comp, (0, HEADC, SKIRTC)))[0]; srcp = co[src]; srcl = comp[src]
pos = srcp[:, 0] >= -0.002
sp_ = srcp[pos]; lab_src = srcl[pos]
def nearest(qp):
    out = np.zeros(len(qp), int)
    for i in range(0, len(qp), 512):
        d = ((qp[i:i + 512, None, :] - sp_[None]) ** 2).sum(-1); out[i:i + 512] = d.argmin(1)
    return out
fcen = bc[bt].mean(1); q = fcen.copy(); q[:, 0] = np.abs(q[:, 0])
fl = lab_src[nearest(q)]
above = (fcen - pc) @ pn > 0
fl = np.where(fl == SKIRTC, 0, fl)
# F7: the head is exactly what lies above the slanted neck plane round the neck/head axis (the seam is the plane's clean cut, not Meshy's
# jagged neckline crease)
hr = np.hypot(fcen[:, 0], fcen[:, 1] + 0.01)
fl = np.where(above & (fcen[:, 2] > NF - 0.06) & (hr < 0.13) & ((fcen[:, 2] > NB + 0.03) | (hr < 0.09)), HEADC, np.where(fl == HEADC, 0, fl))
WAIST = float(os.environ.get('WAIST_Z', '1.10')) + Z0
fl = np.where((fl == 0) & (fcen[:, 2] < WAIST), SKIRTC, fl)
for nm, lb in (('head', HEADC), ('dress', 0), ('skirt', SKIRTC)):
    parts[nm] = mesh(nm, bc, bt[fl == lb]); print('SPLIT', nm, int((fl == lb).sum()))
bpy.data.objects.remove(body, do_unlink=True)
# eyes (+x one paired), lips (mirrored) on the head; lacing pieces on the dress


def join(dst, o):
    c1, t1 = arrays(dst); c2, t2 = arrays(o)
    me = dst.data; me.clear_geometry(); me.from_pydata(np.vstack([c1, c2]).tolist(), [], np.vstack([t1, t2 + len(c1)]).tolist()); me.update()
    bpy.data.objects.remove(o, do_unlink=True)


eye = mesh('eye', co, C(20)); pair(eye); join(parts['head'], eye)
lid = mesh('lid', co, C(24)); pair(lid); join(parts['head'], lid)
for c_ in (21, 22):
    lp = mesh('lip', co, C(c_)); mirror_mid(lp); join(parts['head'], lp)
# hair: the +x half mirrored (Meshy fused its -x braid into the hair; the +x braid is its own shell, dropped: braids are built below)
parts['hair'] = mesh('hair', co, C(11)); mirror_mid(parts['hair'])
# ---- legs: the +x leg with its shoe, onto MM9's foot (x 0.091), cut below the knee
LEGX = float(os.environ.get('LEGX', '0.091'))
lg = mesh('legs', co, C(15)); P = verts(lg)
P[:, 0] += LEGX - 0.5 * (P[P[:, 2] < Z0 + 0.08, 0].min() + P[P[:, 2] < Z0 + 0.08, 0].max())
P[:, 1] += float(os.environ.get('LEGY', '0.0'))
setv(lg, P)
bm = bmesh.new(); bm.from_mesh(lg.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, Z0 + float(os.environ.get('LEGTOP', '0.42'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(lg.data); bm.free(); pair(lg); parts['legs'] = lg
# ---- arm axis from Meshy's +x arm (x 0.29-0.50 after the shift), shoulder on it at MM9's shoulder x
ma = co[comp == 13]; seg_ = ma[(ma[:, 0] > 0.33) & (ma[:, 0] < 0.52)]
cs_ = []
for x in np.linspace(0.34, 0.51, 12):
    s_ = seg_[np.abs(seg_[:, 0] - x) < 0.008]
    if len(s_): cs_.append(0.5 * (s_.min(0) + s_.max(0)))
cs_ = np.array(cs_); m_ = cs_.mean(0); _, _, vt = np.linalg.svd(cs_ - m_); ax = vt[0] * np.sign(vt[0][0])
MM9_SH = np.array([0.163, 0.033, 1.347 + Z0]); MM9_ARM = 0.460; MM9_UA = 0.240
sh = m_ + ax * ((MM9_SH[0] - m_[0]) / ax[0])
print('ARM axis (Meshy)', ax.round(3), 'shoulder', sh.round(3), 'MM9', MM9_SH.round(3), 'deg below horizontal', round(float(np.degrees(np.arcsin(-ax[2]))), 1))
def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K
# Meshy swung the arms ~11 deg forward of MM9's bind arm: the short sleeve beyond the shoulder cap is turned onto MM9's arm direction (as PF8)
MM9_DIR = np.array([float(x) for x in os.environ.get('MM9_DIR', '0.899,-0.057,-0.434').split(',')]); MM9_DIR /= np.linalg.norm(MM9_DIR)
print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))
Pd = verts(parts['dress'])
for sgn in (1, -1):
    a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
    t = (Pd - s0) @ a; kk = ss(t, -0.03, 0.08)
    for i in np.where((Pd[:, 0] * sgn > 0) & (kk > 0))[0]:
        Pd[i] = s0 + rodr(a, m, kk[i]) @ (Pd[i] - s0)
setv(parts['dress'], Pd)
ax = MM9_DIR.copy()
wr = sh + ax * MM9_ARM; el = sh + ax * MM9_UA
# sleeve hem: the furthest dress vertex along the axis near the arm
dc = verts(parts['dress']); t_ = (dc - sh) @ ax; r_ = np.linalg.norm(dc - sh - t_[:, None] * ax, axis=1)
HEM = float(t_[(dc[:, 0] > 0.15) & (r_ < 0.09)].max()); print('SLEEVE hem along the arm', round(HEM, 3))
# ---- MPFB arm: forearm on the axis, thumb forward, palm down; whole arm scaled to a 175 mm hand, wrist on MM9's wrist distance
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0 = np.array(hj['wrist']); e0 = np.array(hj['lowerarm01'])
fa0 = (w0 - e0) / np.linalg.norm(w0 - e0); t0 = np.array(F['t']); t0 -= fa0 * (t0 @ fa0); t0 /= np.linalg.norm(t0)
S = float(os.environ.get('HANDLEN', '0.175')) / F['L']
th = np.array([0, -1.0, 0]); th -= ax * (th @ ax); th /= np.linalg.norm(th)
A = np.c_[fa0, t0, np.cross(fa0, t0)]; B = np.c_[ax, th, np.cross(ax, th)]; Rm = B @ A.T
print('HAND det', round(np.linalg.det(Rm), 4), 'scale', round(S, 4), 'MPFB forearm', round(float(np.linalg.norm(w0 - e0) * S), 3), 'MM9', round(MM9_ARM - MM9_UA, 3))
def tf(p): return (np.atleast_2d(p) - w0) @ Rm.T * S + wr
hq = tf(hc); al = (hq - sh) @ ax
# the upper-arm stub inside the sleeve: cut at STUB from the shoulder, held inside RMAX of the axis beyond the hem
STUB = float(os.environ.get('STUB', '0.075')); RMAX = float(os.environ.get('STUBR', '0.040'))
ht2 = ht[(al[ht] > STUB).all(1)]
rv = hq - sh - al[:, None] * ax; r = np.linalg.norm(rv, axis=1); inside = al < HEM - 0.01; k = inside & (r > RMAX)
hq[k] = sh + al[k, None] * ax + rv[k] / r[k, None] * RMAX
print('ARM faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()), 'upper-arm radius at the hem', round(float(np.percentile(r[np.abs(al - HEM) < 0.01], 90)), 3))
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- bracelets (MM9 F7 paints a copper bracelet on each wrist; Meshy modelled one): a rounded band fitted per angle round the MPFB wrist
fd = ax.copy(); BR_W = float(os.environ.get('BR_W', '0.010')); BR_T = float(os.environ.get('BR_T', '0.003'))
BR_C = float(os.environ.get('BR_C', '-0.012')); BR_GAP = float(os.environ.get('BR_GAP', '0.0012'))
u0 = np.cross(fd, [0, 0, 1.0]); u0 /= np.linalg.norm(u0); v0 = np.cross(fd, u0)
NA, NS = 16, 6
a_ = (hq - wr) @ fd; band_ = hq[np.abs(a_ - BR_C) < 0.5 * BR_W + 0.004]; rel_ = band_ - wr - ((band_ - wr) @ fd)[:, None] * fd
phi_ = np.arctan2(rel_ @ v0, rel_ @ u0); rad_ = np.linalg.norm(rel_, axis=1)
prof = np.zeros(NA)
for i in range(NA):
    ph = 2 * np.pi * i / NA; d_ = np.abs((phi_ - ph + np.pi) % (2 * np.pi) - np.pi); sel_ = d_ < 2 * np.pi / NA * 1.2
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
print('BRACELET radius', round(float(prof.mean()), 4), 'at', BR_C, 'from the wrist')
# ---- holes: open shoe soles and the cut leg tops
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['legs'], 100)
# ---- reduce outside the head: legs freely, the dress with its borders (neck, hood, skirt seams) held, symmetric
BUDGET = dict(legs=int(os.environ.get('B_LEGS', '760')), dress=int(os.environ.get('B_DRESS', '2200')), skirt=int(os.environ.get('B_SKIRT', '1700')))
def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)
for nm, b in BUDGET.items():
    o_ = parts[nm]; t0_ = tris(o_)
    if t0_ <= b * 1.02: continue
    vg = o_.vertex_groups.new(name='free')
    bm = bmesh.new(); bm.from_mesh(o_.data); bm.verts.ensure_lookup_table()
    free = [v.index for v in bm.verts if not any(e.is_boundary for e in v.link_edges)]; bm.free()
    vg.add(free, 1.0, 'REPLACE')
    for x in bpy.data.objects: x.select_set(x is o_)
    bpy.context.view_layer.objects.active = o_
    md = o_.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = b / t0_; md.use_symmetry = True; md.symmetry_axis = 'X'
    md.use_collapse_triangulate = True; md.vertex_group = 'free'; md.vertex_group_factor = 1.0
    bpy.ops.object.modifier_apply(modifier='d'); [o_.vertex_groups.remove(g_) for g_ in list(o_.vertex_groups)]; print('REDUCE', nm, t0_, '->', tris(o_))
# ---- skirt lining: an inner copy 4 mm in, reversed, one rim strip along the hem (a corpse is seen from the feet)
def lining(src, name, depth=0.004, top=Z0 + 0.30):
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
if os.environ.get('LINING', '0') == '1': parts['lining'] = lining(parts['skirt'], 'lining')      # F7: Meshy closed the skirt (inner hem wall + floor at the shins)
# ---- braids (F3's add_parts_pf3.py): a tube along MM9 F7's xpony path from the temple (inside the hair) in front of the shoulder to the
# chest, pushed clear of head/dress by its radius + 4 mm; plait swell and pinch, taper, a tie 2.5 cm above the end, a short tuft; top capped
class cKDTree:
    """chunked brute-force nearest neighbour (Blender has no scipy; the queries here are small)"""
    def __init__(self, P): self.P = np.asarray(P, float)
    def query(self, Q):
        Q = np.atleast_2d(Q); d = np.zeros(len(Q)); ii = np.zeros(len(Q), int)
        for i in range(0, len(Q), 64):
            dd = ((Q[i:i + 64, None, :] - self.P[None]) ** 2).sum(-1); ii[i:i + 64] = dd.argmin(1); d[i:i + 64] = np.sqrt(dd.min(1))
        return d, ii
SBc = []
for nm in ('head', 'dress'):
    c_, t_ = arrays(parts[nm]); SBc += [c_, c_[t_].mean(1)]
SB = np.vstack(SBc); kd = cKDTree(SB)
def spline(pts, n):
    pts = np.array(pts, float); P_ = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]]); out = []
    for k in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[k - 1:k + 3]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1]); return np.array(out)
R0 = float(os.environ.get('BRAID_R', '0.0115')); PITCH, NSb = 0.018, 6; LEN_SCALE = float(os.environ.get('BRAID_LEN', '1.0'))
BX = float(os.environ.get('BRAID_X', '0.072'))
bco, btri, bpar = [], [], []
for sgn in (1, -1):
    ctrl = [[BX - 0.008, 0.004, 0.705], [BX - 0.002, -0.030, 0.640], [BX + 0.001, -0.050, 0.600], [BX + 0.001, -0.080, 0.535], [BX + 0.001, -0.128, 0.445], [BX, -0.165, 0.385], [BX, -0.180, 0.345]]
    ctrl = [[sgn * c[0], c[1], c[2]] for c in ctrl]
    path = spline(ctrl, 40)
    Ls = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]; s = np.arange(0, Ls[-1], PITCH / 3)
    s = np.linspace(0, s[-1] * LEN_SCALE, len(s)); path = np.c_[[np.interp(s, Ls, path[:, k]) for k in range(3)]].T; tot = s[-1]
    def radius(sv):
        r = R0 * (0.75 + 0.25 * np.clip((tot - 0.03 - sv) / 0.06, 0, 1))
        r = r * (0.94 + 0.08 * np.abs(np.sin(np.pi * sv / (PITCH / 2))))
        tie = tot - 0.025; r = np.where(np.abs(sv - tie) < 0.004, R0 * 0.42, r)
        tuft = sv > tie + 0.004; q = (sv - tie - 0.004) / max(tot - tie - 0.004, 1e-6)
        r = np.where(tuft, R0 * (0.55 + 0.55 * np.sin(np.pi * np.clip(q, 0, 1) * 0.85)) * (1 - q ** 3), r)
        return np.maximum(r, 0.0008)
    rr = radius(s)
    for _ in range(120):
        d, ii = kd.query(path); need = rr + 0.004 - d; push = (need > 0) & (s > 0.03)
        if not push.any(): break
        dirv = path - SB[ii]; dirv /= np.maximum(np.linalg.norm(dirv, axis=1, keepdims=True), 1e-9)
        path[push] += dirv[push] * np.minimum(need[push], 0.002)[:, None]
        for _k in range(2): path[1:-1] = 0.5 * path[1:-1] + 0.25 * (path[:-2] + path[2:])
    d, _ = kd.query(path); print('BRAID', sgn, 'length', round(tot, 3), 'clearance mm', round(float((d - rr)[s > 0.03].min() * 1000), 1))
    Tg = np.gradient(path, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True)
    ref = np.array([sgn * 1.0, 0, 0]); N0 = []
    for t_ in Tg:
        nn = ref - (ref @ t_) * t_; nn /= np.linalg.norm(nn); N0.append(nn); ref = nn
    N0 = np.array(N0); B0 = np.cross(Tg, N0); base = sum(len(x) for x in bco)
    th = np.linspace(0, 2 * np.pi, NSb, endpoint=False)
    V = (path[:, None, :] + rr[:, None, None] * (np.cos(th)[None, :, None] * N0[:, None, :] + np.sin(th)[None, :, None] * B0[:, None, :])).reshape(-1, 3)
    F_ = []
    for i in range(len(s) - 1):
        for k in range(NSb):
            a, b, c, d2 = i * NSb + k, i * NSb + (k + 1) % NSb, (i + 1) * NSb + (k + 1) % NSb, (i + 1) * NSb + k
            F_ += [[a, d2, c], [a, c, b]]
    V = np.vstack([V, path[0], path[-1]]); c0, c1 = len(V) - 2, len(V) - 1; last = (len(s) - 1) * NSb
    for k in range(NSb): F_.append([c0, k, (k + 1) % NSb]); F_.append([c1, last + (k + 1) % NSb, last + k])
    F_ = np.array(F_); fcn = V[F_].mean(1); fnn = np.cross(V[F_[:, 1]] - V[F_[:, 0]], V[F_[:, 2]] - V[F_[:, 0]])
    nr = cKDTree(path).query(fcn)[1]
    if (np.einsum('ij,ij->i', fnn, fcn - path[nr]) < 0).mean() > 0.5: F_ = F_[:, ::-1]
    bco.append(V); btri.append(F_ + base); bpar.append(np.r_[s / tot, 0.0, 1.0][np.r_[np.repeat(np.arange(len(s)), NSb), len(s), len(s) + 1]])
parts['braids'] = mesh('braids', np.vstack(bco), np.vstack(btri))
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
         hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], arm_scale=1.0, hem=HEM)
print('SAVED', base, sum(len(t) for t in Tr))
