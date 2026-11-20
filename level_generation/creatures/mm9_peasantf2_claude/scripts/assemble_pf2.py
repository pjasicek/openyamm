"""PF2 (from assemble_pf7.py / assemble_pf1.py): segmented Meshy parts (seg_pf1.py) -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.9297).
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
Z0 = -0.9297; X0 = float(os.environ.get('X0', '0.007'))
D = np.load(SEG); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']
HEADC, SKIRTC = 47, 48; HOODC = -99
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
# PF2: a clean waist cut (plane at WAIST over the torso only; the bell cuffs hang below it at |x| > 0.3)
WZ_ = float(os.environ.get('WAIST_Z', '1.09')) + Z0
bm = bmesh.new(); bm.from_mesh(body.data)
sel = [f for f in bm.faces if abs(f.calc_center_median().x) < 0.30 and abs(f.calc_center_median().z - WZ_) < 0.05]
geo = list({v for f in sel for v in f.verts}) + list({e for f in sel for e in f.edges}) + sel
bmesh.ops.bisect_plane(bm, geom=geo, plane_co=(0, 0, WZ_), plane_no=(0, 0, 1), dist=1e-5)
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
WAIST = float(os.environ.get('WAIST_Z', '1.09')) + Z0
fl = np.where(fl == SKIRTC, 0, fl); fl = np.where((fl == 0) & (fcen[:, 2] < WAIST) & (np.abs(fcen[:, 0]) < 0.30), SKIRTC, fl)      # PF2: not the bell cuffs
for nm, lb in (('head', HEADC), ('dress', 0), ('skirt', SKIRTC)):
    parts[nm] = mesh(nm, bc, bt[fl == lb]); print('SPLIT', nm, int((fl == lb).sum()))
bpy.data.objects.remove(body, do_unlink=True)
# eyes (+x one paired), lips (mirrored) on the head; lacing pieces on the dress


def join(dst, o):
    c1, t1 = arrays(dst); c2, t2 = arrays(o)
    me = dst.data; me.clear_geometry(); me.from_pydata(np.vstack([c1, c2]).tolist(), [], np.vstack([t1, t2 + len(c1)]).tolist()); me.update()
    bpy.data.objects.remove(o, do_unlink=True)


# PF2: Meshy's human ears poke out under the hair cap's side edge (MM9's hair covers them): pressed to the skull, |x| <= EAR_XMAX in the
# ear zone (head verts only; the neck seam is far below)
Ph = verts(parts['head']); EX = float(os.environ.get('EAR_XMAX', '0.068'))
ez = (Ph[:, 2] > 0.60) & (Ph[:, 2] < 0.735) & (Ph[:, 1] > -0.065) & (Ph[:, 1] < 0.035) & (np.abs(Ph[:, 0]) > EX)
w_ = ss(Ph[:, 2], 0.60, 0.625) * (1 - ss(Ph[:, 2], 0.715, 0.735))
Ph[ez, 0] = np.sign(Ph[ez, 0]) * (EX + (np.abs(Ph[ez, 0]) - EX) * (1 - w_[ez]))
# then the whole ear zone Laplacian-smoothed in place (boundary of the zone held), so no ear fold remains under the painted hair
hc0, ht0 = arrays(parts['head']); hc0 = Ph.copy()
zone = (Ph[:, 2] > 0.595) & (Ph[:, 2] < 0.74) & (Ph[:, 1] > -0.07) & (Ph[:, 1] < 0.045) & (np.abs(Ph[:, 0]) > 0.045)
ee = np.vstack([ht0[:, [0, 1]], ht0[:, [1, 2]], ht0[:, [2, 0]]])
for _ in range(int(os.environ.get('EAR_PASSES', '25'))):
    acc = np.zeros_like(Ph); dg = np.zeros(len(Ph)); np.add.at(acc, ee[:, 0], Ph[ee[:, 1]]); np.add.at(dg, ee[:, 0], 1)
    L_ = acc / np.maximum(dg, 1)[:, None]; Ph[zone] = 0.5 * Ph[zone] + 0.5 * L_[zone]
    Ph[zone, 0] = np.sign(Ph[zone, 0]) * np.minimum(np.abs(Ph[zone, 0]), EX)
setv(parts['head'], Ph); print('EARS pressed', int(ez.sum()), 'zone smoothed', int(zone.sum()), 'max move mm', round(float(np.linalg.norm(Ph - hc0, axis=1).max() * 1000), 1))
eye = mesh('eye', co, C(18)); pair(eye); join(parts['head'], eye)
# PF2: Meshy's mouth inserts (seg 24/25, inside the lips) dropped; hair cap + braid + nape tie as the hair part (mirrored from +x)
hr = mesh('hair', co, C(14)); mirror_mid(hr); parts['hair'] = hr
for c_ in (11, 19):
    o_ = mesh('hairp', co, C(c_)); mirror_mid(o_); join(parts['hair'], o_)
# PF2 hair side panel: MM9's hair covers the ears and reaches the jaw at the sides; Meshy's cap stops above the ear. The head surface between
# the cap's edge (+1.2 cm under it) and jaw level, sides only (azimuth 35-128 deg from the back), duplicated 7 mm out along its normals, with a
# rim strip back to the head surface along the panel's open edges; joined to the hair (painted as hair by the head retexture).
CAPZ = np.array([[0, 0.601], [15, 0.600], [30, 0.605], [45, 0.616], [60, 0.612], [75, 0.623], [90, 0.651], [105, 0.647], [120, 0.647], [135, 0.714], [150, 0.752]])
hc_, ht_ = arrays(parts['head']); fcn = hc_[ht_].mean(1); azf = np.degrees(np.arctan2(np.abs(fcn[:, 0]), fcn[:, 1]))
zlo = np.interp(azf, [35, 100, 128], [0.590, 0.585, 0.640]); ztop = np.interp(azf, CAPZ[:, 0], CAPZ[:, 1]) + 0.012
psel = (azf > 35) & (azf < 128) & (fcn[:, 2] > zlo) & (fcn[:, 2] < ztop) & (np.abs(fcn[:, 0]) > 0.03)
if os.environ.get('PANEL', '0') == '1':
    from math import radians
    hv_ = hc_; hph = np.degrees(np.arctan2(np.abs(hv_[:, 0]), hv_[:, 1])); hr_ = np.hypot(hv_[:, 0], hv_[:, 1])
    NU, NV = 16, 9; OFF = float(os.environ.get('PANEL_OFF', '0.007'))
    PH = np.linspace(35, 128, NU); U_ = np.linspace(0, 1, NV)
    ZL = np.interp(PH, [35, 100, 128], [0.590, 0.585, 0.640]); ZT = np.interp(PH, CAPZ[:, 0], CAPZ[:, 1]) + 0.012
    R = np.zeros((NV, NU))
    for i in range(NV):
        for j in range(NU):
            z = ZL[j] + (ZT[j] - ZL[j]) * U_[i]
            m = (np.abs(hph - PH[j]) < 9) & (np.abs(hv_[:, 2] - z) < 0.012)
            R[i, j] = hr_[m].max() if m.any() else np.nan
    R = np.where(np.isnan(R), np.nanmean(R), R)
    R0_ = R.copy()
    for _ in range(4):
        Rp = np.pad(R, 1, mode='edge'); R = 0.5 * R + 0.125 * (Rp[:-2, 1:-1] + Rp[2:, 1:-1] + Rp[1:-1, :-2] + Rp[1:-1, 2:])
    R = np.maximum(R, R0_ - 0.001)
    # offset tapers from OFF under the cap edge to 1.5 mm at the jaw (bottom rows) and the front edge (cheek), so the panel blends into skin
    tv = U_[:, None] ** 0.8; tf = 1 - np.clip((PH[None, :] - 105) / 23, 0, 1)
    OFFG = 0.0015 + (OFF - 0.0015) * tv * (0.4 + 0.6 * tf)
    V = []; T = []
    for sgn in (1, -1):
        base = len(V)
        for i in range(NV):
            for j in range(NU):
                z = ZL[j] + (ZT[j] - ZL[j]) * U_[i]; ph = radians(PH[j]); r = R[i, j] + OFFG[i, j]
                V.append([sgn * r * np.sin(ph), r * np.cos(ph), z])
        for i in range(NV):
            for j in range(NU):
                z = ZL[j] + (ZT[j] - ZL[j]) * U_[i]; ph = radians(PH[j]); r = R[i, j] + 0.0005
                V.append([sgn * r * np.sin(ph), r * np.cos(ph), z])
        o2 = NV * NU
        def vid(i, j, inner=0): return base + inner * o2 + i * NU + j
        for i in range(NV - 1):
            for j in range(NU - 1):
                a_, b_, c_, d_ = vid(i, j), vid(i, j + 1), vid(i + 1, j + 1), vid(i + 1, j)
                T += [[a_, b_, c_], [a_, c_, d_]]
        ring = [(0, j) for j in range(NU)] + [(i, NU - 1) for i in range(1, NV)] + [(NV - 1, j) for j in range(NU - 2, -1, -1)] + [(i, 0) for i in range(NV - 2, 0, -1)]
        for k in range(len(ring)):
            p, q = ring[k], ring[(k + 1) % len(ring)]
            T += [[vid(*p), vid(*q, 1), vid(*q)], [vid(*p), vid(*p, 1), vid(*q, 1)]]
    pn_ = mesh('panel', np.array(V), np.array(T))
    bm = bmesh.new(); bm.from_mesh(pn_.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(pn_.data); bm.free()
    join(parts['hair'], pn_); print('HAIR panel grid', NU, 'x', NV, 'per side, radius', round(float(R.min()), 3), '..', round(float(R.max()), 3))
BEADS = [22, 23] + list(range(26, 33)) + list(range(34, 47))
nk = mesh('necklace', co, C(*BEADS)); mirror_mid(nk); parts['necklace'] = nk
bk = mesh('buckle', co, C(33)); mirror_mid(bk); parts['buckle'] = bk
# ---- legs: the +x leg with its shoe and sole, onto MM9's foot (x 0.091), cut below the knee
LEGX = float(os.environ.get('LEGX', '0.091'))
lg = mesh('legs', co, C(15, 21)); P = verts(lg)
P[:, 0] += LEGX - 0.5 * (P[P[:, 2] < Z0 + 0.08, 0].min() + P[P[:, 2] < Z0 + 0.08, 0].max())
P[:, 1] += float(os.environ.get('LEGY', '0.0'))
setv(lg, P)
bm = bmesh.new(); bm.from_mesh(lg.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, Z0 + float(os.environ.get('LEGTOP', '0.42'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(lg.data); bm.free(); pair(lg); parts['legs'] = lg
# ---- the sleeve axis: centres of x-slices of the dress's +x sleeve before the bell (x 0.24-0.42 after the shift)
dc = verts(parts['dress']); seg_ = dc[(dc[:, 0] > 0.22) & (dc[:, 0] < 0.44) & (dc[:, 2] > Z0 + 0.95)]
cs_ = []
for x in np.linspace(0.24, 0.42, 10):
    s_ = seg_[np.abs(seg_[:, 0] - x) < 0.008]
    if len(s_): cs_.append(0.5 * (s_.min(0) + s_.max(0)))
cs_ = np.array(cs_); m_ = cs_.mean(0); _, _, vt = np.linalg.svd(cs_ - m_); ax = vt[0] * np.sign(vt[0][0])
MM9_SH = np.array([0.163, 0.033, 1.347 + Z0]); MM9_ARM = 0.460
sh = m_ + ax * ((MM9_SH[0] - m_[0]) / ax[0])
mh = co[comp == 13]; wr0 = mh[np.argmin((mh - sh) @ ax)]; tw0 = float((wr0 - sh) @ ax)      # Meshy's +x hand: its nearest point along the axis = the wrist
S_ARM = MM9_ARM / tw0
print('ARM axis', ax.round(3), 'shoulder', sh.round(3), 'deg below horizontal', round(float(np.degrees(np.arcsin(-ax[2]))), 1), 'Meshy wrist t', round(tw0, 3), 'scale', round(S_ARM, 3))
def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K
MM9_DIR = np.array([float(x) for x in os.environ.get('MM9_DIR', '0.825,-0.057,-0.562').split(',')]); MM9_DIR /= np.linalg.norm(MM9_DIR)
print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))
Pd = verts(parts['dress'])
for sgn in (1, -1):
    a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
    t = (Pd - s0) @ a; kk = ss(t, -0.03, 0.08)
    for i in np.where((Pd[:, 0] * sgn > 0) & (kk > 0))[0]:
        q = Pd[i] + a * (max(t[i], 0) * (S_ARM - 1) * kk[i])
        Pd[i] = s0 + rodr(a, m, kk[i]) @ (q - s0)
setv(parts['dress'], Pd)
ax = MM9_DIR.copy(); wr = sh + ax * MM9_ARM
# ---- the bell's closing disc (Meshy capped the cuff round its hand) pressed into a funnel: the faces of the sleeve end that face out along
# the arm move back up the sleeve by FUNNEL x (1 - r / R_end) and in toward the wrist radius, so the cuff reads open with its inside showing
bm = bmesh.new(); bm.from_mesh(parts['dress'].data); bm.normal_update(); bm.verts.ensure_lookup_table()
FUN = float(os.environ.get('FUNNEL', '0.07')); moved = 0
for sgn in (1, -1):
    a = ax * [sgn, 1, 1]; w0_ = wr * [sgn, 1, 1]
    capf = [f for f in bm.faces if (f.calc_center_median() - __import__('mathutils').Vector(w0_)).dot(__import__('mathutils').Vector(a)) > -0.03 and f.normal.dot(__import__('mathutils').Vector(a)) > 0.6 and f.calc_center_median().x * sgn > 0.3]
    cv = {v for f in capf for v in f.verts}
    if not cv: continue
    P_ = np.array([v.co[:] for v in cv]); t_ = (P_ - w0_) @ a; rv = P_ - w0_ - t_[:, None] * a; r_ = np.linalg.norm(rv, axis=1); R = r_.max()
    for v, p, tt, rr, rvv in zip(cv, P_, t_, r_, rv):
        if rr > R - 0.002: continue
        k = 1 - rr / R; nr = 0.018 + (rr / R) * (R - 0.018)
        newp = w0_ + a * (tt - FUN * k) + (rvv / max(rr, 1e-6)) * nr
        v.co = __import__('mathutils').Vector(newp); moved += 1
    print('CUFF', sgn, 'disc verts', len(cv), 'bell radius', round(float(R), 3))
bm.to_mesh(parts['dress'].data); bm.free(); print('FUNNEL moved', moved)
P = verts(parts['dress']); pa = P[P[:, 0] > 0]; tw = (pa - sh) @ ax
ring = pa[np.abs(tw - MM9_ARM) < 0.02]; rr = np.linalg.norm(ring - sh - ((ring - sh) @ ax)[:, None] * ax, axis=1)
print('WRIST', wr.round(3), 'sleeve radius near the wrist', round(float(np.percentile(rr, 10)), 4))
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
STUB = float(os.environ.get('STUB', '0.035')); RMAX = float(os.environ.get('STUBR', '0.020'))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1)
kk = np.clip(-al / 0.012, 0, 1); lim = RMAX + (r - RMAX) * (1 - kk); k = r > lim
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * lim[k, None]
rw = r[(al > -0.004) & (al < 0.004)]
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()), 'stub radius', round(RMAX, 4), 'hand radius at wrist', round(float(rw.max()), 4) if len(rw) else None)
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- holes: open shoe soles and the cut leg tops
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['legs'], 100)
# ---- reduce outside the head: legs freely, the dress with its borders (neck, hood, skirt seams) held, symmetric
BUDGET = dict(legs=int(os.environ.get('B_LEGS', '760')), dress=int(os.environ.get('B_DRESS', '2600')), skirt=int(os.environ.get('B_SKIRT', '1600')), necklace=int(os.environ.get('B_NECK', '900')))
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
if os.environ.get('LINING', '0') == '1': parts['lining'] = lining(parts['skirt'], 'lining')
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
         hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], arm_scale=S_ARM, hem=0.0)
print('SAVED', base, sum(len(t) for t in Tr))
