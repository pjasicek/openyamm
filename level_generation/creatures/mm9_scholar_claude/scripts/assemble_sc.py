"""Bembridge Scholar: raw Meshy parts (step1_clean.py) -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at
z = -0.8986, SCHOLAR.abc's Bip01 skeleton). After Igrid's assemble_wo.py and the Monk's assemble.py.
- ROBE: the robe shell with its stole collar, mirrored from the +x half; sleeves turned and scaled onto MM9's arm.
- HEAD: the face shell mirrored (+x half), Meshy's eye pieces replaced by fitted spheres. HAIR: hair + beard shell mirrored.
- CAP: as Meshy made it (MM9's cap is tilted to one side too). JEWEL: medallion, buckle, chain beads (as made).
- LEGS: the +x shoe on MM9's foot, paired, with a plain shin tube to below the knee (hidden by the robe).
- HANDS: posed MPFB male hands with a forearm stub into the sleeve.
Args: <raw npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
RAW, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
Z0 = -0.8986; X0 = float(os.environ.get('X0', '0.008'))
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
parts['robe'] = mesh('robe', co, C(0)); mirror_mid(parts['robe'])
hd = mesh('head', co, C(1)); mirror_mid(hd)
ED = co[comp == 10]; EYE_R = float(os.environ.get('EYE_R', '0.0118'))
EYE_C = np.array([abs(ED[:, 0].mean()), ED[:, 1].min() + EYE_R * float(os.environ.get('EYE_IN', '1.0')), ED[:, 2].mean()])
EYE_C[0] = float(os.environ.get('EYE_X', EYE_C[0]))
print('EYE centre', EYE_C.round(4), 'r', EYE_R)
hP, hT = arrays(hd)
for sgn in (1, -1):
    c_ = EYE_C * [sgn, 1, 1]; r_ = np.linalg.norm(hP - c_, axis=1); k_ = r_ < EYE_R + 0.0006
    hP[k_] = c_ + (hP[k_] - c_) / r_[k_, None] * (EYE_R + 0.0006)
    print('EYE rim pushed', int(k_.sum()))
setv(hd, hP)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=EYE_R)
for v in bm.verts: v.co = v.co + Vector(EYE_C)
bmesh.ops.triangulate(bm, faces=bm.faces)
me_ = bpy.data.meshes.new('eye'); bm.to_mesh(me_); bm.free(); eye = bpy.data.objects.new('eye', me_); coll.objects.link(eye)
pair(eye); join(hd, eye); parts['head'] = hd
hr = mesh('hair', co, C(4)); mirror_mid(hr); parts['hair'] = hr
parts['cap'] = mesh('cap', co, C(7))
small = [c for c in np.unique(comp) if c >= 8 and c not in (9, 10)]
parts['jewel'] = mesh('jewel', co, C(*small))
LEGX = float(os.environ.get('LEGX', '0.134')); LEGY = float(os.environ.get('LEGY', '0.0'))
sh_ = mesh('legs', co, C(5)); P = verts(sh_)
low = P[:, 2] < Z0 + 0.06
P[:, 0] += LEGX - 0.5 * (P[low, 0].min() + P[low, 0].max()); P[:, 1] += LEGY
setv(sh_, P)
top = P[P[:, 2] > P[:, 2].max() - 0.015]; c0 = top.mean(0); r0 = float(np.linalg.norm((top - c0)[:, :2], axis=1).mean())
print('SHOE top ring', c0.round(3), round(r0, 3))
N = 10; rings = [(c0 + [0, 0, -0.02], r0 * 0.95), (c0 + [0, 0, 0.10], r0 * 1.0), (np.array([LEGX - 0.01, c0[1] + 0.02, Z0 + 0.58]), r0 * 1.25)]
V = []; T = []
for i, (c_, r_) in enumerate(rings):
    for k in range(N):
        a = 2 * np.pi * k / N; V.append(c_ + [r_ * np.cos(a), r_ * np.sin(a), 0])
    if i:
        for k in range(N):
            a, b = (i - 1) * N + k, (i - 1) * N + (k + 1) % N; T += [[a, b, b + N], [a, b + N, a + N]]
c_ = rings[-1][0]; V.append(c_); ci = len(V) - 1
for k in range(N): T.append([2 * N + k, 2 * N + (k + 1) % N, ci])
shin = mesh('shin', np.array(V), np.array(T)); join(sh_, shin); pair(sh_); parts['legs'] = sh_
# ---- sleeve axis (+x) from section centroids
rc, rt = arrays(parts['robe'])
d = np.array([float(x) for x in os.environ.get('SLEEVE_D', '0.86,-0.27,-0.45').split(',')]); d /= np.linalg.norm(d)
p = np.array([float(x) for x in os.environ.get('SLEEVE_P', '0.26,0.05,1.35').split(',')]) + [0, 0, Z0]; line = []
for i in range(30):
    l = nearest_loop(section(rc, rt, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > .08: break
    line.append(l['c']); p = l['c'] + d * .02
line = np.array(line)
ax = line[-3] - line[1]; ax /= np.linalg.norm(ax)
print('SLEEVE line', len(line), line[0].round(3), line[-1].round(3), 'axis', ax.round(3))
MM9_SH = np.array([0.219, 0.04, 0.481]); MM9_HAND = np.array([0.698, 0.03, 0.274])
MM9_ARM = float(np.linalg.norm(MM9_HAND - MM9_SH)); MM9_DIR = (MM9_HAND - MM9_SH) / MM9_ARM
sh = line[0] + ax * ((MM9_SH[0] - line[0][0]) / ax[0])
RSL = float(os.environ.get('RSLEEVE', '0.16'))
dP = verts(parts['robe']); tt = (dP - sh) @ ax; rr = np.linalg.norm(dP - sh - tt[:, None] * ax, axis=1)
tend = float(tt[(dP[:, 0] > 0.15) & (rr < RSL)].max())
S_ARM = (MM9_ARM + float(os.environ.get('CUFFOVER', '0.0'))) / tend
print('SHOULDER on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'cuff end t', round(tend, 3), 'arm scale', round(S_ARM, 3))


def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


print('ARM turn onto MM9 direction deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))


def pull(o):
    P = verts(o)
    for sgn in (1, -1):
        a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
        t = (P - s0) @ a; r = np.linalg.norm(P - s0 - t[:, None] * a, axis=1)
        side = np.where((P[:, 0] * sgn > 0.12) & (r < RSL + 0.04))[0]
        k = ss(t, -0.02, 0.10) * (1 - ss(r, RSL, RSL + 0.04))
        for i in side:
            if k[i] <= 0: continue
            q = P[i] + a * (max(t[i], 0) * (S_ARM - 1) * k[i])
            P[i] = s0 + rodr(a, m, k[i]) @ (q - s0)
    setv(o, P)


pull(parts['robe'])
ax = MM9_DIR.copy()
wr = sh + ax * MM9_ARM
print('WRIST', wr.round(3))
# ---- hands: posed MPFB, fingers along the arm axis, thumb forward, palm down; the forearm stub through the cuff
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd_, t0 = [np.array(F[k]) for k in ('w', 'hd', 't')]
S = float(os.environ.get('HANDLEN', '0.195')) / F['L']
fd = ax.copy(); th = np.array([0, -1.0, 0]); th -= fd * (th @ fd); th /= np.linalg.norm(th)
A = np.c_[hd_, t0, np.cross(hd_, t0)]; nz = np.cross(fd, th); B = np.c_[fd, th, nz]
Rm = B @ A.T


def tf0(p): return (np.asarray(p) - w0) @ Rm.T * S + wr


hq0 = tf0(hc); al = (hq0 - wr) @ fd; beh = hq0[al < -0.04]; sd = (wr - beh.mean(0)); sd /= np.linalg.norm(sd)


def tf(p):
    p = np.atleast_2d(tf0(p)); a = (p - wr) @ fd; k = np.clip((0.03 - a) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
    return np.array([wr + rodr(sd, fd, k[i]) @ (p[i] - wr) for i in range(len(p))])


hq = tf(hc); al = (hq - wr) @ fd
STUB = float(os.environ.get('STUB', '0.07')); RMAX = float(os.environ.get('STUBR', '0.024'))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1); k = (al < -0.005) & (r > RMAX)
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * RMAX
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()))
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o


def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()


fill(parts['legs'], 100)
BUDGET = dict(legs=int(os.environ.get('B_LEGS', '520')), robe=int(os.environ.get('B_ROBE', '5200')), hair=int(os.environ.get('B_HAIR', '1800')),
              cap=int(os.environ.get('B_CAP', '500')), jewel=int(os.environ.get('B_JEWEL', '700')))


def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)


for nm, b in BUDGET.items():
    o_ = parts[nm]; t0_ = tris(o_)
    if t0_ <= b * 1.02: print('KEEP', nm, t0_); continue
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
         hand_co=hq, hand_W=Hd['W'], hand_bones=Hd['bones'], arm_scale=S_ARM, eye_c=EYE_C, eye_r=EYE_R)
print('SAVED', base, sum(len(t) for t in Tr))
