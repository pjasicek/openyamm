"""Wyrde: segmented Meshy parts (seg_wy.py) -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at
z = -0.9297, the human female skeleton shared with PeasantF1). From PF1's assemble_pf1.py (fused shell split by labels) and PF8's
assemble_pf.py (long sleeves pulled to MM9's wrist, MPFB hand with a forearm stub into the cuff).
- The fused shell (head, hair, hood, cowl, mantle, gown) is mirrored as one (+x half), then split: HEAD SET = face, neck, hair,
  circlet and the hood above its fold (behind the face a straight cut at BACK_Z, bisected, so the hood/cowl texture seam is a clean
  line in the fold), MANTLE = cowl and mantle, DRESS = gown with its sleeves (closed cuff caps kept: the hand stub passes through).
- Eyes (+x paired) on the head; jewellery (pendant, choker beads, belt stone, panel ornaments) as one unmirrored part.
- Underskirt mirrored with a 4 mm lining; legs: Meshy's +x leg on MM9's foot, cut below the knee; Meshy's hands replaced.
Args: <seg npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
SEG, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
Z0 = -0.9297; X0 = float(os.environ.get('X0', '0.008'))
D = np.load(SEG); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']; labels = [str(x) for x in D['labels']]
L = {n: 100 + i for i, n in enumerate(labels)}
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


def join(dst, o):
    c1, t1 = arrays(dst); c2, t2 = arrays(o)
    me = dst.data; me.clear_geometry(); me.from_pydata(np.vstack([c1, c2]).tolist(), [], np.vstack([t1, t2 + len(c1)]).tolist()); me.update()
    bpy.data.objects.remove(o, do_unlink=True)


parts = {}
# ---- the fused shell: mirror, the straight hood/cowl cut behind the face, split by label
SH = list(L.values())
body = mesh('body', co, C(*SH)); mirror_mid(body)
BACK_Z = float(os.environ.get('BACK_Z', '1.465')) + Z0; BACK_Y = float(os.environ.get('BACK_Y', '-0.03'))
bm = bmesh.new(); bm.from_mesh(body.data)
sel = [f for f in bm.faces if f.calc_center_median().y > BACK_Y - 0.02 and abs(f.calc_center_median().z - BACK_Z) < 0.05]
geo = list({v for f in sel for v in f.verts}) + list({e for f in sel for e in f.edges}) + sel
bmesh.ops.bisect_plane(bm, geom=geo, plane_co=(0, 0, BACK_Z), plane_no=(0, 0, 1), dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(body.data); bm.free()
bc, bt = arrays(body)
src = np.where(np.isin(comp, SH))[0]; srcp = co[src]; srcl = comp[src]
pos = srcp[:, 0] >= -0.002; sp_ = srcp[pos]; lab_src = srcl[pos]
def nearest(qp):
    out = np.zeros(len(qp), int)
    for i in range(0, len(qp), 512):
        d = ((qp[i:i + 512, None, :] - sp_[None]) ** 2).sum(-1); out[i:i + 512] = d.argmin(1)
    return out
fcen = bc[bt].mean(1)
# face label = majority of its three vertices' labels (nearest source vertex, mirrored): the boundary follows edges, no teeth
qv = bc.copy(); qv[:, 0] = np.abs(qv[:, 0]); vl = lab_src[nearest(qv)][bt]
fl = np.where(vl[:, 1] == vl[:, 2], vl[:, 1], vl[:, 0])
HEADSET = (L['head'], L['hair'], L['hood'])
back = fcen[:, 1] > BACK_Y
above = fcen[:, 2] > BACK_Z
grp = np.where(np.isin(fl, HEADSET), 0, np.where(fl == L['mantle'], 1, 2))
# behind the face: the hood above the cut is the head set, the cowl and anything of the hood below it the mantle
grp = np.where(back & (grp != 2) & above, 0, grp)
grp = np.where(back & (grp == 0) & ~above, 1, grp)
# label islands: one smoothing vote over face neighbours (single faces of another label inside a region)
e2f = {}
for i, t in enumerate(bt):
    for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): e2f.setdefault((min(a, b), max(a, b)), []).append(i)
nb = [[] for _ in range(len(bt))]
for fs in e2f.values():
    if len(fs) == 2: nb[fs[0]].append(fs[1]); nb[fs[1]].append(fs[0])
for _ in range(2):
    g2 = grp.copy()
    for i in range(len(bt)):
        if len(nb[i]) >= 2:
            v = [grp[j] for j in nb[i]]
            if all(x != grp[i] for x in v) and len(set(v)) == 1 and not (back[i] and abs(fcen[i, 2] - BACK_Z) < 0.01): g2[i] = v[0]
    grp = g2
for nm, k in (('head', 0), ('mantle', 1), ('dress', 2)):
    parts[nm] = mesh(nm, bc, bt[grp == k]); print('SPLIT', nm, int((grp == k).sum()))
bpy.data.objects.remove(body, do_unlink=True)
# ---- head geometry before the paint (positions only on the shell): Meshy's small human ears (MM9's hood and hair hide them) pressed
# into the side of the head; the spiky socket rims relaxed (at most 2.5 mm) and kept outside the new eyeball
def laplace(P, t, passes, k=0.5):
    e = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0); n = len(P)
    deg = np.zeros(n); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1); S = P.copy()
    for _ in range(passes):
        acc = np.zeros_like(S); np.add.at(acc, e[:, 0], S[e[:, 1]]); np.add.at(acc, e[:, 1], S[e[:, 0]])
        S = (1 - k) * S + k * acc / np.maximum(deg, 1)[:, None]
    return S
EC = np.array([float(x) for x in os.environ.get('EAR_C', '0.074,-0.030,0.665').split(',')])
EYE_C = np.array([float(x) for x in os.environ.get('EYE_C', '0.0226,-0.0943,0.6803').split(',')]); EYE_R = float(os.environ.get('EYE_R', '0.0143'))
hP, hT = arrays(parts['head'])
# the ear: only face-skin vertices (seg label head) near the ear centre move, as a membrane over the zone with its border fixed
qa = hP.copy(); qa[:, 0] = np.abs(qa[:, 0]); skin = lab_src[nearest(qa)] == L['head']
ear = skin & (np.linalg.norm(qa - EC, axis=1) < float(os.environ.get('EAR_R', '0.034')))
eE = np.unique(np.sort(np.vstack([hT[:, [0, 1]], hT[:, [1, 2]], hT[:, [2, 0]]]), axis=1), axis=0)
degE = np.zeros(len(hP)); np.add.at(degE, eE[:, 0], 1); np.add.at(degE, eE[:, 1], 1); M = hP.copy()
for _ in range(300):
    acc = np.zeros_like(M); np.add.at(acc, eE[:, 0], M[eE[:, 1]]); np.add.at(acc, eE[:, 1], M[eE[:, 0]])
    M[ear] = (0.5 * M + 0.5 * acc / np.maximum(degE, 1)[:, None])[ear]
print('EARS flattened', int(ear.sum()), 'verts, moved max', round(float(np.linalg.norm(M - hP, axis=1).max()), 4)); hP = M
S6 = laplace(hP, hT, 6); q = hP.copy(); q[:, 0] = np.abs(q[:, 0]); de = np.linalg.norm(q - EYE_C, axis=1)
ws = 1 - ss(de, 0.016, 0.022); dv = (S6 - hP) * ws[:, None]; nrm = np.linalg.norm(dv, axis=1); dv *= (np.minimum(nrm, 0.0025) / np.maximum(nrm, 1e-9))[:, None]
hP = hP + dv
for sgn in (1, -1):
    c_ = EYE_C * [sgn, 1, 1]; r_ = np.linalg.norm(hP - c_, axis=1); k_ = (r_ < EYE_R + 0.0006) & (ws > 0)
    hP[k_] = c_ + (hP[k_] - c_) / r_[k_, None] * (EYE_R + 0.0006)
print('SOCKETS relaxed', int((ws > 0.5).sum()), 'verts')
setv(parts['head'], hP)
# eyes: smooth spheres fitted to Meshy's lumpy +x eyeball (comp 7 -> 17), paired
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=EYE_R)
for v in bm.verts: v.co = v.co + Vector(EYE_C)
bmesh.ops.triangulate(bm, faces=bm.faces)
me_ = bpy.data.meshes.new('eye'); bm.to_mesh(me_); bm.free(); eye = bpy.data.objects.new('eye', me_); coll.objects.link(eye)
pair(eye); join(parts['head'], eye)
# jewellery: pendant 19, belt stone 18, panel ornaments 20/21 (the +x one paired), choker beads 22.. (as Meshy made them)
jw = mesh('jewel', co, C(18, 19, *range(22, 60)))
orn = mesh('orn', co, C(21)); pair(orn); join(jw, orn); parts['jewel'] = jw
parts['skirt'] = mesh('skirt', co, C(11)); mirror_mid(parts['skirt'])
# ---- legs: the +x leg with its shoe (comp 4 -> 14), onto MM9's foot (x 0.091), cut below the knee
LEGX = float(os.environ.get('LEGX', '0.091'))
lg = mesh('legs', co, C(14)); P = verts(lg)
P[:, 0] += LEGX - 0.5 * (P[P[:, 2] < Z0 + 0.08, 0].min() + P[P[:, 2] < Z0 + 0.08, 0].max())
P[:, 1] += float(os.environ.get('LEGY', '0.0'))
setv(lg, P)
bm = bmesh.new(); bm.from_mesh(lg.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, Z0 + float(os.environ.get('LEGTOP', '0.42'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(lg.data); bm.free(); pair(lg); parts['legs'] = lg
# ---- sleeve axis (on the dress, +x side) from section centroids
rc, rt = arrays(parts['dress'])
d = np.array([.82, -0.17, -.55]); d /= np.linalg.norm(d); p = np.array([.24, -.015, 1.31 + Z0]); line = []
for i in range(24):
    l = nearest_loop(section(rc, rt, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > .07: break
    line.append(l['c']); p = l['c'] + d * .02
line = np.array(line)
ax = line[-3] - line[1]; ax /= np.linalg.norm(ax)
print('SLEEVE line', len(line), line[0].round(3), line[-1].round(3), 'axis', ax.round(3))
MM9_SH = np.array([0.163, 0.033, 1.347 + Z0]); MM9_ARM = 0.458
sh = line[0] + ax * ((MM9_SH[0] - line[0][0]) / ax[0])
dP = verts(parts['dress']); tt = (dP - sh) @ ax; rr = np.linalg.norm(dP - sh - tt[:, None] * ax, axis=1)
tend = float(tt[(dP[:, 0] > 0.15) & (rr < 0.10)].max())
S_ARM = (MM9_ARM + float(os.environ.get('CUFFOVER', '0.0'))) / tend
print('SHOULDER on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'cuff end t', round(tend, 3), 'arm scale', round(S_ARM, 3))
def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K
MM9_DIR = np.array([0.382, -0.026, -0.255]); MM9_DIR /= np.linalg.norm(MM9_DIR)
print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))
def pull(o):
    """the sleeve beyond the shoulder cap: scaled along the axis to MM9's length and turned onto MM9's arm direction"""
    P = verts(o)
    for sgn in (1, -1):
        a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
        t = (P - s0) @ a; r = np.linalg.norm(P - s0 - t[:, None] * a, axis=1)
        side = np.where((P[:, 0] * sgn > 0.12) & (r < 0.13))[0]
        k = ss(t, -0.02, 0.10)
        for i in side:
            if k[i] <= 0: continue
            q = P[i] + a * (max(t[i], 0) * (S_ARM - 1) * k[i])
            P[i] = s0 + rodr(a, m, k[i]) @ (q - s0)
    setv(o, P)
pull(parts['dress'])
ax = MM9_DIR.copy()
wr = sh + ax * MM9_ARM
print('WRIST', wr.round(3))
# ---- hands: posed MPFB, fingers along the arm axis, thumb forward, palm down; the forearm stub through the cuff cap
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd, t0 = [np.array(F[k]) for k in ('w', 'hd', 't')]
S = float(os.environ.get('HANDLEN', '0.172')) / F['L']
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
STUB = float(os.environ.get('STUB', '0.06')); RMAX = float(os.environ.get('STUBR', '0.024'))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1); k = (al < -0.005) & (r > RMAX)
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * RMAX
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()))
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- holes: the open shoe soles and the cut leg tops
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['legs'], 100)
# ---- reduce outside the head: borders held (part seams), symmetric
BUDGET = dict(legs=int(os.environ.get('B_LEGS', '600')), dress=int(os.environ.get('B_DRESS', '2600')), mantle=int(os.environ.get('B_MANTLE', '1700')),
              skirt=int(os.environ.get('B_SKIRT', '1100')), jewel=int(os.environ.get('B_JEWEL', '900')))
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
    md = o_.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = b / t0_; md.use_collapse_triangulate = True
    if nm != 'jewel': md.use_symmetry = True; md.symmetry_axis = 'X'
    md.vertex_group = 'free'; md.vertex_group_factor = 1.0
    bpy.ops.object.modifier_apply(modifier='d'); [o_.vertex_groups.remove(g_) for g_ in list(o_.vertex_groups)]; print('REDUCE', nm, t0_, '->', tris(o_))
# ---- underskirt lining: an inner copy 4 mm in, reversed, one rim strip along the hem
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
# the underskirt's hem is closed (Meshy made it a solid): no lining needed
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
