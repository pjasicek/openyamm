"""Raw Meshy parts -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.4797, as PEASANTGIRL2).
From PeasantF5's assemble_pf5.py. Meshy returned the face, dress, sleeves (closed bell cuffs), apron and skirt as ONE shell (comp 0), the
hair helmet (1) with a scalp cap (4), two hands, shoes, shins, eyeballs, two braid ties and two belt buttons.
- The head sits 5.5 mm to -x of the body midline (eyes, nose): shifted onto x = 0 with a feather over the neck, then every shell is bisected
  at x = 0 and its +x half mirrored (the +x eyeball is kept in the head and mirrored).
- A needle strip Meshy hung from the lips to the chest is dropped (faces with an edge over 8 cm and aspect over 60).
- comp 0 is reduced outside the head (vertex group), then split: head (z over the level neck cut ZC), skirt (below the belt, |x| < 0.22),
  dress (bodice and sleeves).
- Sleeves pulled along the sleeve axis to MM9's arm length and turned onto MM9's arm direction (radially limited: the torso side stays);
  Meshy's hands dropped; posed MPFB hands (child length) at MM9's wrist with a short stub inside the closed bell cuff.
- Legs: Meshy's shins and shoes, mirrored. Skirt lining (inner copy 4 mm in) with rims at the hem and the apron's lower edge.
- Optional elf ears (EARS=1 default): a procedural cupped leaf (F8's) out through the hair as MM9's PeasantGirl1e; kept as its own part
  'ears' so the human GLB can leave it out.
Args: <raw npz> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
RAW, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
Z0 = -0.4797
D = np.load(RAW); co, tri, comp = D['co'].copy(), D['tri'], D['comp']
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
# ---- head onto the body midline
HX = float(os.environ.get('HX', '0.0055'))
HEADC = (1, 4, 7, 8, 9, 10)
co[:, 0] += np.where(np.isin(comp, HEADC), HX, np.where(comp == 0, HX * ss(co[:, 2], 1.00, 1.06), 0.0))
co = co + [0, 0, Z0]
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


def arrays(o):
    me = o.data; me.calc_loop_triangles(); return verts(o), np.array([lt.vertices[:] for lt in me.loop_triangles])


def tris(o): return sum(len(p_.vertices) - 2 for p_ in o.data.polygons)


def decimate(o, budget, group=None):
    t0_ = tris(o)
    if t0_ <= budget * 1.02: print('KEEP', o.name, t0_); return
    for x in bpy.data.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = budget / t0_; md.use_symmetry = True; md.symmetry_axis = 'X'
    md.use_collapse_triangulate = True
    if group: md.vertex_group = group
    bpy.ops.object.modifier_apply(modifier='d'); print('REDUCE', o.name, t0_, '->', tris(o))


# ---- comp 0 without the lip-to-chest needle strip, eyeball +x kept with it
t0 = C(0)
a_, b_, c_ = co[t0[:, 0]], co[t0[:, 1]], co[t0[:, 2]]
L_ = np.stack([np.linalg.norm(b_ - a_, axis=1), np.linalg.norm(c_ - b_, axis=1), np.linalg.norm(a_ - c_, axis=1)], 1)
ar_ = 0.5 * np.linalg.norm(np.cross(b_ - a_, c_ - a_), axis=1); asp = L_.max(1) ** 2 / np.maximum(ar_, 1e-12)
cen_ = (a_ + b_ + c_) / 3
needle = (L_.max(1) > 0.06) & (asp > 40) & (np.abs(cen_[:, 0]) < 0.07) & (cen_[:, 2] > Z0 + 0.78) & (cen_[:, 2] < Z0 + 1.12)
print('NEEDLE faces dropped', int(needle.sum()))
body = mesh('body', co, np.vstack([t0[~needle], C(7)]))
mirror_mid(body)
# the needle's lip / chest ends may leave stray single faces: keep the largest connected piece and the eyeballs
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
seen = set(); comps_ = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); ids = []
    while st:
        x = st.pop(); ids.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps_.append(ids)
drop = [ids for ids in comps_ if len(ids) < 40]
print('BODY pieces', sorted(len(i) for i in comps_)[-6:], 'dropped', sum(len(i) for i in drop))
for ids in drop:
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in ids], context='VERTS'); bm.verts.ensure_lookup_table()
bm.to_mesh(body.data); bm.free()
# ---- reduce the body outside the head (and the neck seam)
ZC = Z0 + float(os.environ.get('ZC', '1.050'))
P = verts(body)
vg = body.vertex_groups.new(name='red'); vg.add([i for i in range(len(P)) if P[i, 2] < ZC - 0.03], 1.0, 'REPLACE')
decimate(body, int(os.environ.get('BODY_BUDGET', '6800')), 'red')
# ---- split: head above ZC, skirt below the belt
ZW = Z0 + float(os.environ.get('ZW', '0.752'))
bm = bmesh.new(); bm.from_mesh(body.data); g_ = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g_, plane_co=(0, 0, ZC), plane_no=(0, 0, 1), dist=1e-5); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(body.data); bm.free()
c, t = arrays(body); cen = c[t].mean(1)        # a level neck seam: the head / body material edge is a straight line
eyes_ = np.zeros(len(t), bool)
fh = cen[:, 2] > ZC
fs = (cen[:, 2] < ZW) & (np.abs(cen[:, 0]) < 0.22)
parts = {}
parts['head'] = mesh('head', c, t[fh]); parts['skirt'] = mesh('skirt', c, t[fs]); parts['dress'] = mesh('dress', c, t[~fh & ~fs])
bpy.data.objects.remove(body)
hair = mesh('hair', co, C(1, 4)); mirror_mid(hair); parts['hair'] = hair
# the braid ties (comps 9, 10) are dropped: without modelled braids they hang beside the jaw like earrings
btn = mesh('buttons', co, C(14)); pair(btn); parts['buttons'] = btn
# ---- legs: the +x shin and shoe, a touch back onto MM9's foot
lg = mesh('legs', co, C(11, 5)); P = verts(lg); P[:, 1] += float(os.environ.get('LEGY', '0.010')); setv(lg, P); pair(lg); parts['legs'] = lg
# ---- sleeve axis from x-plane sections of the dress (+x)
dc, dt = arrays(parts['dress'])
cs = []
for x in np.arange(0.15, 0.29, 0.01):
    ls = [l for l in section(dc, dt, np.array([x, 0, 0]), np.array([1.0, 0, 0])) if l['c'][2] > Z0 + 0.5]
    if ls: cs.append(min(ls, key=lambda l: l['per'])['c'])
cs = np.array(cs); mc = cs.mean(0); _, _, vt = np.linalg.svd(cs - mc); ax = vt[0] * np.sign(vt[0][0])
MM9_SH = np.array([0.145, 0.025, 0.438]); MM9_WR = np.array([0.430, 0.017, 0.249])
MM9_ARM = float(np.linalg.norm(MM9_WR - MM9_SH)); MM9_DIR = (MM9_WR - MM9_SH) / MM9_ARM
sh = mc + ax * ((MM9_SH[0] - mc[0]) / ax[0])
pa = dc[dc[:, 0] > 0.1]; tend = float(((pa - sh) @ ax).max())
CUFF = float(os.environ.get('CUFF', '0.012'))          # the wrist sits this far inside the cuff's end
S_ARM = (MM9_ARM + CUFF) / tend
print('ARM axis', ax.round(3), 'shoulder on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'cuff end t', round(tend, 3), 'MM9 arm', round(MM9_ARM, 3),
      'arm scale', round(S_ARM, 3), 'turn deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))


def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


def pull(o):
    """beyond the shoulder cap, near the sleeve axis: scaled along the axis to MM9's length and turned onto MM9's arm direction"""
    P = verts(o)
    for sgn in (1, -1):
        a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
        t = (P - s0) @ a; r = np.linalg.norm(P - s0 - t[:, None] * a, axis=1)
        k = ss(t, -0.02, 0.06) * (1 - ss(r, 0.085, 0.12) * (1 - ss(t, 0.10, 0.16)))
        for i in np.where((P[:, 0] * sgn > 0) & (k > 0))[0]:
            q = P[i] + a * (max(t[i], 0) * (S_ARM - 1) * k[i])
            P[i] = s0 + rodr(a, m, k[i]) @ (q - s0)
    setv(o, P)


pull(parts['dress'])
ax = MM9_DIR.copy(); wr = sh + ax * MM9_ARM
P = verts(parts['dress']); pa = P[P[:, 0] > 0.1]; tw = (pa - sh) @ ax
ring = pa[(tw > MM9_ARM - 0.03) & (tw < MM9_ARM)]; rr = np.linalg.norm(ring - sh - ((ring - sh) @ ax)[:, None] * ax, axis=1)
print('WRIST', wr.round(3), 'cuff ring n', len(rr), 'cuff end t', round(float(tw.max()), 3), 'tw pct', np.percentile(tw, [50, 90, 99]).round(3))
# ---- hands: posed MPFB, fingers along the arm axis, thumb forward, palm down
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd, t0_ = [np.array(F[k]) for k in ('w', 'hd', 't')]
S = float(os.environ.get('HANDLEN', '0.135')) / F['L']
fd = ax.copy(); th = np.array([0, -1.0, 0]); th -= fd * (th @ fd); th /= np.linalg.norm(th)
A = np.c_[hd, t0_, np.cross(hd, t0_)]; nz = np.cross(fd, th); B = np.c_[fd, th, nz]
Rm = B @ A.T
print('HAND det', round(np.linalg.det(Rm), 4), 'scale', round(S, 4))
def tf0(p): return (np.asarray(p) - w0) @ Rm.T * S + wr
hq0 = tf0(hc); al = (hq0 - wr) @ fd; beh = hq0[al < -0.03]; sd = (wr - beh.mean(0)); sd /= np.linalg.norm(sd)
def tf(p):
    p = np.atleast_2d(tf0(p)); a = (p - wr) @ fd; k = np.clip((0.03 - a) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
    return np.array([wr + rodr(sd, fd, k[i]) @ (p[i] - wr) for i in range(len(p))])
hq = tf(hc); al = (hq - wr) @ fd
STUB = float(os.environ.get('STUB', '0.030')); RMAX = float(os.environ.get('STUBR', '0.020'))
ht2 = ht[(al[ht] > -STUB).all(1)]
rv = hq - wr - al[:, None] * fd; r = np.linalg.norm(rv, axis=1)
kk = np.clip(-al / 0.012, 0, 1); lim = RMAX + (r - RMAX) * (1 - kk); k = r > lim
hq[k] = wr + al[k, None] * fd + rv[k] / r[k, None] * lim[k, None]
rw = r[(al > -0.004) & (al < 0.004)]
print('HAND stub faces kept', len(ht2), 'of', len(ht), 'clamped', int(k.sum()), 'hand radius at wrist', round(float(rw.max()), 4) if len(rw) else None)
o = mesh('hands', hq, ht2); hj2 = {k_: tf(np.array(v))[0].tolist() for k_, v in hj.items()}
pair(o); parts['hands'] = o
# ---- elf ears (part 'ears'): a cupped leaf with a rim, root inside the head under the hair, tip out and up through the hair (MM9 Girl1e:
# root (0.063, -0.025, 1.14) over the soles, tip (0.104, -0.015, 1.192))
if os.environ.get('EARS', '1') == '1':
    ER = np.array([float(x) for x in os.environ.get('EAR_ROOT', '0.066,-0.015,1.130').split(',')]) + [0, 0, Z0]
    eu = np.array([float(x) for x in os.environ.get('EAR_DIR', '0.66,0.12,0.74').split(',')]); eu /= np.linalg.norm(eu)
    en = np.array([1.0, -0.55, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)
    ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
    EL = float(os.environ.get('EAR_LEN', '0.080')); EW = float(os.environ.get('EAR_W', '0.034'))
    NU, NV = 12, 7
    uu = np.linspace(0, 1, NU); vv = np.linspace(-1, 1, NV)
    V = []; T = []
    for side, sgn in (('front', 1), ('back', -1)):
        for i, u in enumerate(uu):
            wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
            th_ = 0.0045 * (1 - u) ** 0.7 + 0.0010
            for j, v in enumerate(vv):
                cup = 0.005 * (1 - v * v) * np.sin(np.pi * min(u * 1.1, 1)) if sgn > 0 else 0.0
                rim = 0.0016 * np.exp(-((abs(v) - 1) / 0.3) ** 2) * (1 - u) if sgn > 0 else 0.0
                off = sgn * th_ * np.sqrt(max(1 - v * v, 0.0)) - cup + rim
                V.append(ER + eu * (u * EL) + ev * (v * wid * 0.5) + en * off)
    nf = NU * NV
    for s in (0, 1):
        for i in range(NU - 1):
            for j in range(NV - 1):
                a = s * nf + i * NV + j; b = a + 1; c_ = a + NV; d_ = c_ + 1
                T += [[a, b, d_], [a, d_, c_]] if s == 0 else [[a, d_, b], [a, c_, d_]]
    for i in range(NU - 1):
        for j in (0, NV - 1):
            a, c_ = i * NV + j, (i + 1) * NV + j; b, d_ = nf + a, nf + c_
            T += [[a, c_, d_], [a, d_, b]] if j == 0 else [[a, d_, c_], [a, b, d_]]
    V = np.array(V); V[(NU - 1) * NV:nf] = V[(NU - 1) * NV:nf].mean(0); V[nf + (NU - 1) * NV:] = V[(NU - 1) * NV:nf].mean(0)
    ear = mesh('ears', V, np.array(T))
    bm = bmesh.new(); bm.from_mesh(ear.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(ear.data); bm.free()
    pair(ear); parts['ears'] = ear
# ---- holes: the shin tops and bottoms
def fill(o, sides):
    bm = bmesh.new(); bm.from_mesh(o.data)
    r = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=sides)
    bmesh.ops.triangulate(bm, faces=r['faces']); print('FILLED', o.name, len(r['faces'])); bm.to_mesh(o.data); bm.free()
fill(parts['legs'], 100)
for nm, b in dict(hair=int(os.environ.get('HAIR_BUDGET', '1300')), legs=560).items(): decimate(parts[nm], b)
# ---- skirt lining: an inner copy 4 mm in, reversed, rim strips along the hem and the apron's lower edge (open loops below TOP)
def lining(src, name, depth=0.004, top=Z0 + 0.70):
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
