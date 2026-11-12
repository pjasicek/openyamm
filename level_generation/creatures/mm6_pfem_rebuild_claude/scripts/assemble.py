"""MM6 PeasantF1 rebuild: the v3 body (work/v3.npz from extract_v3.py) -> symmetric labelled parts in MM9's PeasantFemale frame
(Blender frame: faces -Y, z up; MM9's origin, soles at z = Z0), for the MM9 skeleton and clips. After mm9_peasantf1_claude/scripts/assemble_pf1.py.
- Scale S so the v3 Head joint sits at MM9's Head height; the whole figure shifted onto x = 0 (Meshy left it 7.5 mm off), the braid on its own.
- Symmetric (the user asked for it): body shell, skirt, belt, hair and circlet keep the figure's right half (x < 0) and are mirrored; legs paired
  from the right leg; braid and buckle stay as they are (centred).
- Arms: the bare v3 arm (thin, open Meshy hand) is cut at the short sleeve's hem; the sleeve beyond the shoulder cap is turned onto MM9's bind
  arm direction (the v3 A-pose hangs 25 deg lower and swung back); a posed, straightened MPFB female arm (work/hand.npz, mpfb_arm.py:
  upper-arm stub inside the sleeve, forearm, five-finger hand) on that axis, v3's shoulder-to-wrist length, paired.
- Hair: Meshy's sawtooth rims relaxed along the rim.
- Reduce per part (borders held, symmetric), skirt lining 4 mm in (reduced), hem rim strip.
- co_up: the same vertices in the v3 arm pose (sleeves and arms turned back), for the Meshy upload: the HD masters show that pose.
Args: <v3 npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
V3, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
Z0 = -0.9297
MM9_HEAD = 0.562
D = np.load(V3); J3 = {k: np.array(v) for k, v in json.loads(str(D['joints'])).items()}
S = (MM9_HEAD - Z0) / J3['mixamorig:Head'][2]
co0 = D['co'].copy(); tri0 = D['tri']; part0 = D['part']; head0 = D['head']; col0 = D['col']
fc0 = co0[tri0].mean(1)
torso = (part0 == 0) & (head0 == 0) & (fc0[:, 2] > 1.05) & (fc0[:, 2] < 1.33)
cs = []
for z in np.arange(1.06, 1.32, 0.02):
    q = co0[tri0[torso & (np.abs(fc0[:, 2] - z) < 0.01)].ravel()]
    q = q[np.abs(q[:, 0]) < 0.14]
    if len(q): cs.append(0.5 * (q[:, 0].min() + q[:, 0].max()))
DX = -float(np.median(cs))
# the face has its own midline (mirror test on the front of the face: best at x = -8 mm, the torso's at -2.6 mm): mirroring the head
# about the torso's line split the nose off-centre (a two-lobed nose). The shift follows the head above the neck, blended over the neck.
hv0 = np.unique(tri0[(part0 == 0) & (head0 == 1)]); fq = co0[hv0]; fq = fq[(fq[:, 1] < -0.04) & (fq[:, 2] > 1.37) & (fq[:, 2] < 1.53)]
cand = np.arange(-0.016, 0.004, 0.0005)
_nn = lambda a, b: np.sqrt(((a[:, None, :] - b[None]) ** 2).sum(-1)).min(1)
err = [np.median(_nn(fq * [-1, 1, 1] + [2 * c, 0, 0], fq)) for c in cand]
DXH = -float(cand[int(np.argmin(err))])
print('SCALE', round(S, 4), 'shift x torso', round(DX * 1000, 2), 'mm, head', round(DXH * 1000, 2), 'mm')
def dxz(z): t = np.clip((z - 1.30) / 0.07, 0, 1); t = t * t * (3 - 2 * t); return DX + (DXH - DX) * t
def tf(p):
    p = np.atleast_2d(p).astype(float).copy(); p[:, 0] += dxz(p[:, 2]); return p * S + [0, 0, Z0]
co = tf(co0); JJ = {k: tf(v)[0] for k, v in J3.items()}
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def mesh(name, c, t, lab=None):
    u, inv = np.unique(t.ravel(), return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[u].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    if lab is not None: me.attributes.new('lab', 'INT', 'FACE').data.foreach_set('value', np.asarray(lab, int).tolist())
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    return o


def arrays(o, lab=False):
    me = o.data; me.calc_loop_triangles()
    c = np.array([v.co[:] for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    if not lab: return c, t
    fl = np.zeros(len(me.polygons), int)
    if 'lab' in me.attributes: me.attributes['lab'].data.foreach_get('value', fl)
    return c, t, fl[[lt.polygon_index for lt in me.loop_triangles]]


def mirror_mid(o):
    """bisect at x = 0, keep x <= 0, add the mirror image (reversed winding), weld the midline; face labels carried"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, clear_inner=False, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    c, t, fl = arrays(o, True)
    c[np.abs(c[:, 0]) < 1e-4, 0] = 0
    n = len(c); mid = np.abs(c[:, 0]) < 1e-9
    idx = np.arange(n) + n; idx[mid] = np.where(mid)[0]
    c2 = np.vstack([c, c * [-1, 1, 1]]); t2 = np.vstack([t, idx[t][:, ::-1]]); l2 = np.r_[fl, fl]
    used, inv = np.unique(t2.ravel(), return_inverse=True)
    me.clear_geometry(); me.from_pydata(c2[used].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    me.attributes.new('lab', 'INT', 'FACE').data.foreach_set('value', l2.tolist())


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


def rodr(a, b, k):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


def poly(q, pts):
    best = np.full(len(q), 1e9); s = np.zeros(len(q)); L0 = 0
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a; L = np.linalg.norm(ab); t = np.clip((q - a) @ ab / L / L, -0.5, 1.5); dd = np.linalg.norm(q - a - np.outer(t, ab), axis=1)
        k = dd < best; best[k] = dd[k]; s[k] = L0 + t[k] * L; L0 += L
    return s, best


rep = {'scale': S, 'dx': DX}
fc = co[tri0].mean(1)
# ---- the v3 right arm (x < 0): sleeve hem by colour along the arm polyline; skin beyond it is cut
SH, EL, WR = JJ['mixamorig:RightArm'], JJ['mixamorig:RightForeArm'], JJ['mixamorig:RightHand']
skinc = (col0[:, 0] - col0[:, 2]) > 0.25
body = (part0 == 0) & (head0 == 0)
t_arm, r_arm = poly(fc, [SH, EL, WR])
near = body & (fc[:, 0] < -0.10) & (r_arm < 0.085)
HEM = float(np.percentile(t_arm[near & ~skinc & (t_arm < 0.25)], 99.5))
cut = body & (fc[:, 0] < -0.10) & (r_arm < 0.09) & ((t_arm > HEM + 0.004) | (skinc & (t_arm > HEM - 0.012)))
rep['hem_t'] = HEM; rep['arm_faces_cut'] = int(cut.sum())
print('HEM along the v3 arm', round(HEM, 3), 'cut faces', int(cut.sum()))
# ---- the mouth closed: the v3 lips part over a 4.5 cm cavity with teeth (Meshy painted an open mouth on it). Cavity vertices (more than
# 4 mm behind the local front surface inside the mouth box) move onto the surface spanned by the lips' rim (inverse-distance in x, z)
hv = np.unique(tri0[(part0 == 0) & (head0 == 1)]); ch = co[hv]
MZ0, MZ1 = 0.574, 0.595
box = (np.abs(ch[:, 0]) < 0.026) & (ch[:, 2] > MZ0) & (ch[:, 2] < MZ1) & (ch[:, 1] < -0.015)
front = np.array([ch[box & (np.abs(ch[:, 0] - p[0]) < 0.004) & (np.abs(ch[:, 2] - p[2]) < 0.003), 1].min() for p in ch[box]]) if box.any() else []
cav = np.zeros(len(ch), bool); cav[np.where(box)[0]] = ch[box, 1] > front + 0.004
cavg = set(hv[cav].tolist())
rep['mouth_cavity_vertices'] = int(cav.sum()); print('MOUTH cavity', int(cav.sum()))
# ---- the shell (face skin label 1, rest 0) minus the arm, mirrored
keep = (part0 == 0) & ~cut & (fc[:, 0] < 0.03)
labs = head0[keep].copy(); labs[np.array([any(v in cavg for v in t) for t in tri0[keep]])] = 2
shell = mesh('shell', co, tri0[keep], lab=labs)
bm = bmesh.new(); bm.from_mesh(shell.data); ll = bm.faces.layers.int['lab']
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[ll] == 2], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
inm = lambda v: abs(v.co.x) < 0.03 and MZ0 - 0.004 < v.co.z < MZ1 + 0.004 and v.co.y < -0.04
hole = [e for e in bm.edges if e.is_boundary and inm(e.verts[0]) and inm(e.verts[1])]
r_ = bmesh.ops.holes_fill(bm, edges=hole, sides=200); nf = r_['faces']
bmesh.ops.triangulate(bm, faces=nf, quad_method='BEAUTY', ngon_method='BEAUTY')
nf2 = [f for f in bm.faces if f[ll] == 0 and all(inm(v) for v in f.verts) and any(e.is_boundary is False for e in f.edges)]
for f in bm.faces:
    if all(inm(v) for v in f.verts): f[ll] = 1
print('MOUTH filled', len(hole), 'rim edges', len(nf), 'faces')
bm.to_mesh(shell.data); bm.free()
mirror_mid(shell)
parts = {}
for nm, pids in (('skirt', [7]), ('belt', [5]), ('hair', [8]), ('band', [10])):
    o = mesh(nm, co, tri0[np.isin(part0, pids) & (fc[:, 0] < 0.03)]); mirror_mid(o); parts[nm] = o
bc = co.copy(); bx = 0.5 * (bc[np.unique(tri0[part0 == 9]), 0].min() + bc[np.unique(tri0[part0 == 9]), 0].max())
bc[:, 0] -= bx
parts['braid'] = mesh('braid', bc, tri0[part0 == 9])
parts['buckle'] = mesh('buckle', co, tri0[part0 == 6])
lg = mesh('legs', co, tri0[part0 == 4]); pair(lg); parts['legs'] = lg
# ---- hair rims: Meshy's sawtooth relaxed along the rim (3 passes, midline held)
for nm in ('hair',):
    bm = bmesh.new(); bm.from_mesh(parts[nm].data)
    for _ in range(4):
        mv = {}
        for v in bm.verts:
            nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
            if len(nb) == 2 and abs(v.co.x) > 1e-4: mv[v] = v.co * 0.5 + (nb[0].co + nb[1].co) * 0.25
        for v, c in mv.items(): v.co = c
    bm.to_mesh(parts[nm].data); bm.free()
# ---- sleeves onto MM9's bind arm direction; the +x side is the mirror
MM9_DIR = np.array([-0.382, -0.026, -0.255]); MM9_DIR /= np.linalg.norm(MM9_DIR)
u3 = (EL - SH) / np.linalg.norm(EL - SH)
Rfull = rodr(u3, MM9_DIR, 1.0)
rep['sleeve_turn_deg'] = float(np.degrees(np.arccos(np.clip(u3 @ MM9_DIR, -1, 1))))
print('SLEEVE turn deg', round(rep['sleeve_turn_deg'], 1))
Ps = verts(shell); Pup = Ps.copy()
for sgn in (-1, 1):
    a = u3 * [1 if sgn < 0 else -1, 1, 1]
    s0 = SH * [1 if sgn < 0 else -1, 1, 1]; m = MM9_DIR * [1 if sgn < 0 else -1, 1, 1]
    t = (Ps - s0) @ a; kk = ss(t, -0.03, 0.08)
    for i in np.where((Ps[:, 0] * sgn > 0.05) & (kk > 0))[0]:
        Ps[i] = s0 + rodr(a, m, kk[i]) @ (Ps[i] - s0)
setv(shell, Ps)
# ---- MPFB arm on the +x side (the MPFB .L arm is the figure's left, at +x when facing -Y), then paired
sh = SH * [-1, 1, 1]; ax = MM9_DIR * [-1, 1, 1]
ARM = float(np.linalg.norm(EL - SH) + np.linalg.norm(WR - EL)); UA = float(np.linalg.norm(EL - SH))
wr = sh + ax * ARM; el = sh + ax * UA
dc = verts(shell); t_ = (dc - sh) @ ax; r_ = np.linalg.norm(dc - sh - t_[:, None] * ax, axis=1)
HEMA = float(t_[(dc[:, 0] > 0.12) & (r_ < 0.09)].max()); print('SLEEVE hem along the MM9 axis', round(HEMA, 3), 'arm', round(ARM, 3), 'upper', round(UA, 3))
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0 = np.array(hj['wrist']); e0 = np.array(hj['lowerarm01'])
fa0 = (w0 - e0) / np.linalg.norm(w0 - e0); t0 = np.array(F['t']); t0 -= fa0 * (t0 @ fa0); t0 /= np.linalg.norm(t0)
HS = float(os.environ.get('HANDLEN', '0.172')) / F['L']
th = np.array([0, -1.0, 0]); th -= ax * (th @ ax); th /= np.linalg.norm(th)
A = np.c_[fa0, t0, np.cross(fa0, t0)]; B = np.c_[ax, th, np.cross(ax, th)]; Rm = B @ A.T
print('HAND det', round(np.linalg.det(Rm), 4), 'scale', round(HS, 4), 'MPFB forearm', round(float(np.linalg.norm(w0 - e0) * HS), 3), 'ours', round(ARM - UA, 3))
def tfh(p): return (np.atleast_2d(p) - w0) @ Rm.T * HS + wr
hq = tfh(hc); al = (hq - sh) @ ax
STUB = float(os.environ.get('STUB', '0.06')); RMAX = float(os.environ.get('STUBR', '0.040'))
ht2 = ht[(al[ht] > STUB).all(1)]
rv = hq - sh - al[:, None] * ax; r = np.linalg.norm(rv, axis=1); inside = al < HEMA - 0.01; k = inside & (r > RMAX)
hq[k] = sh + al[k, None] * ax + rv[k] / r[k, None] * RMAX
rep['arm_radius_mm'] = {f'{x:.2f}': round(float(np.percentile(r[np.abs(al - x) < 0.008], 90)) * 1000, 1) for x in (HEMA, UA, ARM - 0.03)}
print('ARM faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()), 'radius p90 mm at hem/elbow/wrist', rep['arm_radius_mm'])
ho = mesh('hands', hq, ht2); pair(ho); parts['hands'] = ho
hj2 = {k_: tfh(np.array(v))[0].tolist() for k_, v in hj.items()}
# ---- reduce outside the face: per part, borders held, symmetric about x
BUD = json.loads(os.environ.get('BUDGET', '{}'))
BUDGET = dict(skirt=1250, hair=760, braid=900, band=150, belt=150, buckle=80, legs=300, hands=1800)
BUDGET.update(BUD)


def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)


def reduce(o_, b, sym=True, protect=None):
    t0_ = tris(o_)
    if t0_ <= b * 1.02: return t0_
    vg = o_.vertex_groups.new(name='free')
    bm = bmesh.new(); bm.from_mesh(o_.data); bm.verts.ensure_lookup_table()
    free = [v.index for v in bm.verts if not any(e.is_boundary for e in v.link_edges) and not (protect is not None and protect(v))]; bm.free()
    vg.add(free, 1.0, 'REPLACE')
    for x in bpy.data.objects: x.select_set(x is o_)
    bpy.context.view_layer.objects.active = o_
    md = o_.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = b / t0_; md.use_symmetry = sym; md.symmetry_axis = 'X'
    md.use_collapse_triangulate = True; md.vertex_group = 'free'; md.vertex_group_factor = 1.0
    bpy.ops.object.modifier_apply(modifier='d'); [o_.vertex_groups.remove(g_) for g_ in list(o_.vertex_groups)]
    return tris(o_)


rep['reduce'] = {}
for nm, b in BUDGET.items():
    t0_ = tris(parts[nm]); rep['reduce'][nm] = [t0_, reduce(parts[nm], b, sym=nm not in ('braid', 'buckle'))]
# the shell: the face (label 1) and the neck under it kept, the torso reduced to its budget
B_SHELL = int(os.environ.get('B_SHELL', '3500'))
t0_ = tris(shell)
me = shell.data; fl = np.zeros(len(me.polygons), int); me.attributes['lab'].data.foreach_get('value', fl)
facev = set(v for p in me.polygons if fl[p.index] == 1 for v in p.vertices)
rep['reduce']['shell'] = [t0_, reduce(shell, B_SHELL, protect=lambda v: v.index in facev)]
print('REDUCE', rep['reduce'])
# ---- split the shell: head (face skin) / dress
c, t, fl = arrays(shell, True)
parts['head'] = mesh('head', c, t[fl == 1]); parts['dress'] = mesh('dress', c, t[fl != 1])
bpy.data.objects.remove(shell, do_unlink=True)


# ---- skirt lining: an inner copy 4 mm in, reversed, reduced, plus a rim strip at the hem
def lining(src, name, depth=0.004, frac=0.5):
    me = src.data; bm = bmesh.new(); bm.from_mesh(me); bm.normal_update(); bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]); n = np.array([v.normal[:] for v in bm.verts])
    t = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
    o = mesh(name, c - n * depth, t[:, ::-1])
    reduce(o, int(len(t) * frac))
    # rim strip: hem boundary of the skirt to the lining's hem boundary (nearest)
    ci, ti = arrays(o)
    def hem_edges(cc, tt, top):
        e = np.sort(np.r_[tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]], axis=1); u, cnt = np.unique(e, axis=0, return_counts=True)
        b = u[cnt == 1]; return b[(cc[b[:, 0], 2] < top) & (cc[b[:, 1], 2] < top)]
    top = c[:, 2].min() + 0.15
    eo = hem_edges(c, t, top); ei = hem_edges(ci, ti, top)
    iu = np.unique(ei); cq = ci[iu]
    near = lambda p: iu[int(np.argmin(((cq - p) ** 2).sum(1)))]
    T = []; N = len(ci)
    for a, b in eo:
        ia = near(c[a]); ib = near(c[b])
        T += [[a + N, b + N, ib], [a + N, ib, ia]] if ia != ib else [[a + N, b + N, ib]]
    T = np.array(T); allc = np.vstack([ci, c])
    nz = np.cross(allc[T[:, 1]] - allc[T[:, 0]], allc[T[:, 2]] - allc[T[:, 0]])[:, 2]
    T[nz > 0] = T[nz > 0][:, ::-1]
    allt = np.vstack([ti, T])
    bpy.data.objects.remove(o, do_unlink=True)
    o = mesh(name, allc, allt)
    bm = bmesh.new(); bm.from_mesh(o.data); bm.normal_update()
    # orient the rim faces outward-down like the hem
    bm.to_mesh(o.data); bm.free()
    print('LINING', name, len(ti), '+ rim', len(T))
    return o


parts['lining'] = lining(parts['skirt'], 'lining')
for k_ in ('legs', 'hands'):
    bm = bmesh.new(); bm.from_mesh(parts[k_].data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(parts[k_].data); bm.free()
for o_ in parts.values():
    for p_ in o_.data.polygons: p_.use_smooth = True
# ---- the upload pose: sleeves and arms turned back to the v3 A pose about each shoulder (the HD masters' pose)
names = ['head', 'hair', 'braid', 'band', 'dress', 'belt', 'buckle', 'skirt', 'lining', 'legs', 'hands']
Co = []; Tr = []; Pa = []; Up = []; base = 0
for k, nm in enumerate(names):
    c, t = arrays(parts[nm]); cu = c.copy()
    if nm in ('dress', 'hands'):
        for sgn in (-1, 1):
            s0 = SH * [1 if sgn < 0 else -1, 1, 1]; m = MM9_DIR * [1 if sgn < 0 else -1, 1, 1]; a = u3 * [1 if sgn < 0 else -1, 1, 1]
            tt = (c - s0) @ m; kk = ss(tt, -0.03, 0.08) if nm == 'dress' else np.ones(len(c))
            for i in np.where((c[:, 0] * sgn > 0.05) & (kk > 0))[0]:
                cu[i] = s0 + rodr(m, a, kk[i]) @ (c[i] - s0)
    Co.append(c); Up.append(cu); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
    print('PART', nm, len(c), len(t))
rep['parts'] = {nm: int(len(t)) for nm, t in zip(names, Tr)}; rep['tris'] = int(sum(len(t) for t in Tr))
np.savez(OUT, co=np.vstack(Co), co_up=np.vstack(Up), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names), sh=sh, wr=wr, el=el, ax=ax,
         hj=json.dumps(hj2), hand_scale=HS, hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], hem=HEMA, scale=S, dx=DX,
         v3joints=json.dumps({k: v.tolist() for k, v in JJ.items()}))
json.dump(rep, open(OUT.replace('.npz', '.json'), 'w'), indent=1)
print('ASSEMBLED', base, rep['tris'])
