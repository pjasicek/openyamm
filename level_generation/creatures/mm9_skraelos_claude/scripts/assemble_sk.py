"""Skraelos: raw Meshy parts (step1_clean.py) -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (pelvis at 0,
soles at z = -0.885, SKRAELOS.abc's thigh-less human female skeleton). After Igrid's assemble_wo.py.
- ROBE: the fused shell (black robe, open rust tabard, sleeves; comp 0) mirrored from the +x half; sleeves turned and scaled onto MM9's arm.
- HOOD: comp 2 mirrored; its long backward point compressed toward MM9's (behind the skull, y > HOOD_Y0, scaled by HOOD_S).
- HEAD: the skull-only Smart Topology (skull_prep.py npz) placed on the Meshy face's eye line, mirrored; Meshy's face, eyes and bead
  necklace dropped. A dark cowl tube under the skull (inside the hood) down into the collar.
- HANDS: the +x skeletal hand (palm comp 7 + 31 bone pieces, four digits) + a fifth digit (copy of the outer finger, offset and scaled),
  moved with the sleeve, mirrored. Per-vertex hand piece ids and the digit chains are saved for the rig.
- NECKLACE: procedural bone fangs on a cord round the collar + a small skull pendant (the skull mesh scaled).
Args: <raw npz> <skull npz or -> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
RAW, SKULL, OUT = sys.argv[sys.argv.index('--') + 1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
E = lambda k, d: float(os.environ.get(k, d))
Z0 = -0.885; Y0 = E('Y0', '0.16'); X0 = E('X0', '0.0')
D = np.load(RAW); co, tri, comp = D['co'] + [X0, Y0, Z0], D['tri'], D['comp']
MJ = json.load(open(os.path.join(os.path.dirname(OUT), 'mm9_joints.json')))
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
    return np.array([v.co[:] for v in me.vertices]).reshape(-1, 3), np.array([lt.vertices[:] for lt in me.loop_triangles]).reshape(-1, 3)


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


def verts(o): return np.array([v.co[:] for v in o.data.vertices])


def setv(o, P):
    for v, p in zip(o.data.vertices, P): v.co = Vector(p)
    o.data.update()


def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K


def raw_mesh(name, c, t):
    me = bpy.data.meshes.new(name); me.from_pydata(np.asarray(c).tolist(), [], np.asarray(t).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o); return o


parts = {}
# ---- robe, mirrored from +x
parts['robe'] = mesh('robe', co, C(0)); mirror_mid(parts['robe'])
# ---- hood, mirrored; the backward point compressed toward MM9's (MM9's hood reaches y 0.217 behind the pelvis plane)
hood = mesh('hood', co, C(2)); mirror_mid(hood)
P = verts(hood); HY0 = E('HOOD_Y0', '0.0'); HS = E('HOOD_S', '0.45')
b = P[:, 1] > HY0; P[b, 1] = HY0 + (P[b, 1] - HY0) * HS
HZ0 = E('HOOD_Z0', '0.70'); HZS = E('HOOD_ZS', '0.80'); bz = b & (P[:, 2] > HZ0)
P[bz, 2] = HZ0 + (P[bz, 2] - HZ0) * (1 - (1 - HZS) * ss(P[bz, 1], HY0, HY0 + 0.15))
setv(hood, P); parts['hood'] = hood
print('HOOD y', P[:, 1].min().round(3), P[:, 1].max().round(3), 'z', P[:, 2].min().round(3), P[:, 2].max().round(3))
# ---- hands (+x): palm + bone pieces; a fifth digit copied from the outer finger
HAND_PIECES = [7, 8, 10, 13, 16, 24, 25, 29, 30, 31, 34, 36, 39, 40, 46, 47, 50, 53, 54, 58, 59, 60, 62, 63, 68, 69, 73, 74, 75, 78, 80, 81]
CHAINS = {'Thumb': [24, 16, 10, 39, 73], 'Index': [59, 75, 80, 81, 36, 40, 29, 47], 'Middle': [74, 53, 60, 46, 13, 34, 69, 50],
          'Ring': [8, 30, 25, 31, 54, 63]}
CARPAL = [7, 58, 62, 68, 78]
hc_list = []; hp_list = []; ht_list = []; base = 0
for k in HAND_PIECES:
    vid = np.where(comp == k)[0]; m = {v: i for i, v in enumerate(vid)}
    t = tri[np.isin(tri[:, 0], vid)]
    hc_list.append(co[vid]); ht_list.append(np.vectorize(m.get)(t) + base); hp_list.append(np.full(len(vid), k)); base += len(vid)
hc = np.vstack(hc_list); ht = np.vstack(ht_list); hp = np.concatenate(hp_list)
cen = {k: hc[hp == k].mean(0) for k in HAND_PIECES}
fdir = cen[CHAINS['Ring'][-1]] - cen[CHAINS['Ring'][0]]; fdir /= np.linalg.norm(fdir)
lat = cen[CHAINS['Ring'][-1]] - cen[CHAINS['Middle'][-1]]; lat -= fdir * (lat @ fdir); lat /= np.linalg.norm(lat)
PO = E('PINKY_OFF', '0.019'); PS = E('PINKY_S', '0.84'); piv = cen[CHAINS['Ring'][0]]
pk_ids = []
for k in CHAINS['Ring']:
    sel = np.where(hp == k)[0]; m = {v: i for i, v in enumerate(sel)}
    t = ht[np.isin(ht[:, 0], sel)]
    q = piv + (hc[sel] - piv) * PS + lat * PO + np.array([0, 0, 0.004])
    nid = 1000 + k; pk_ids.append(nid)
    ht = np.vstack([ht, np.vectorize(m.get)(t) + len(hc)]); hc = np.vstack([hc, q]); hp = np.concatenate([hp, np.full(len(sel), nid)])
CHAINS['Pinky'] = pk_ids
# reduce the bone pieces (each stays a separate piece; labels recovered per connected component by the nearest piece centre)
HR = E('HAND_RATIO', '0.45')
if HR < 1:
    ho = raw_mesh('hand_tmp', hc, ht)
    for x in bpy.data.objects: x.select_set(x is ho)
    bpy.context.view_layer.objects.active = ho
    bm = bmesh.new(); bm.from_mesh(ho.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(ho.data); bm.free()
    md = ho.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = HR; md.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='d')
    oc = {k: hc[hp == k].mean(0) for k in np.unique(hp)}
    hc_new, ht_new = arrays(ho); bpy.data.objects.remove(ho, do_unlink=True)
    par = np.arange(len(hc_new))
    def fnd(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for t in ht_new: a_ = fnd(t[0]); par[fnd(t[1])] = a_; par[fnd(t[2])] = a_
    root = np.array([fnd(i) for i in range(len(hc_new))]); hp_new = np.zeros(len(hc_new), int)
    keys = np.array(list(oc)); cents = np.array([oc[k] for k in keys])
    for r_ in np.unique(root):
        m_ = root == r_; hp_new[m_] = keys[np.argmin(np.linalg.norm(cents - hc_new[m_].mean(0), axis=1))]
    print('HAND reduce', len(ht), '->', len(ht_new), 'pieces', len(np.unique(hp_new)), 'of', len(keys))
    hc, ht, hp = hc_new, ht_new, hp_new
print('PINKY lateral', lat.round(3))
# ---- sleeve axis (+x) from section centroids, turned and scaled onto MM9's arm
rc, rt = arrays(parts['robe'])
d = np.array([float(x) for x in os.environ.get('SLEEVE_D', '0.70,-0.09,-0.70').split(',')]); d /= np.linalg.norm(d)
p = np.array([float(x) for x in os.environ.get('SLEEVE_P', '0.25,0.0,0.32').split(',')]); line = []
for i in range(40):
    l = nearest_loop(section(rc, rt, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > .08: break
    line.append(l['c']); p = l['c'] + d * .02
line = np.array(line)
ax = line[-3] - line[1]; ax /= np.linalg.norm(ax)
print('SLEEVE line', len(line), line[0].round(3), line[-1].round(3), 'axis', ax.round(3))
MM9_SH = np.array(MJ['FHP R UpperArm']); MM9_HAND = np.array(MJ['FHP R Hand'])
MM9_ARM = float(np.linalg.norm(MM9_HAND - MM9_SH)); MM9_DIR = (MM9_HAND - MM9_SH) / MM9_ARM
sh = line[0] + ax * ((MM9_SH[0] - line[0][0]) / ax[0])
RSL = E('RSLEEVE', '0.16')
dP = verts(parts['robe']); tt = (dP - sh) @ ax; rr = np.linalg.norm(dP - sh - tt[:, None] * ax, axis=1)
tend = float(tt[(dP[:, 0] > 0.15) & (rr < RSL)].max())
S_ARM = (MM9_ARM + E('CUFFOVER', '0.0')) / tend
print('SHOULDER on axis', sh.round(3), 'MM9', MM9_SH.round(3), 'cuff end t', round(tend, 3), 'arm scale', round(S_ARM, 3),
      'turn deg', round(float(np.degrees(np.arccos(ax @ MM9_DIR))), 1))


def pull_pts(P, sgn, rigid_t=None):
    a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; m = MM9_DIR * [sgn, 1, 1]
    t = (P - s0) @ a; r = np.linalg.norm(P - s0 - t[:, None] * a, axis=1)
    out = P.copy()
    if rigid_t is not None:   # the hand: a rigid move with the cuff end (translation along the axis, then the full turn)
        q = P + a * (rigid_t * (S_ARM - 1)); return (s0 + (rodr(a, m, 1.0) @ (q - s0).T).T)
    side = np.where((P[:, 0] * sgn > 0.12) & (r < RSL + 0.04))[0]
    k = ss(t, -0.02, 0.10) * (1 - ss(r, RSL, RSL + 0.04))
    for i in side:
        if k[i] <= 0: continue
        q = P[i] + a * (max(t[i], 0) * (S_ARM - 1) * k[i])
        out[i] = s0 + rodr(a, m, k[i]) @ (q - s0)
    return out


RP = verts(parts['robe']); RP = pull_pts(RP, 1); RP = pull_pts(RP, -1); setv(parts['robe'], RP)
hc = pull_pts(hc, 1, rigid_t=tend)
ax = MM9_DIR.copy(); wr = sh + ax * MM9_ARM
print('WRIST', wr.round(3), 'palm centre now', hc[hp == 7].mean(0).round(3))
# mirror the hand
n0 = len(hc); hc2 = np.vstack([hc, hc * [-1, 1, 1]]); ht2 = np.vstack([ht, ht[:, ::-1] + n0]); hp2 = np.concatenate([hp, -hp - 1])
parts['hands'] = raw_mesh('hands', hc2, ht2)
# ---- cap: a dark disc inside the robe (at CAP_Z) so no view under the hem or into the falling robe sees up into the hood
rc2, rt2 = arrays(parts['robe']); CZ = E('CAP_Z', '-0.30')
loops = section(rc2, rt2, np.array([0, 0, CZ]), np.array([0, 0, 1.0])); lp = max(loops, key=lambda l: l['per'])
pts_ = lp['pts']; cc = pts_.mean(0); angp = np.arctan2(pts_[:, 1] - cc[1], pts_[:, 0] - cc[0]); pts_ = pts_[np.argsort(angp)]
NC = 24; sel_ = np.linspace(0, len(pts_), NC, endpoint=False).astype(int); ring = pts_[sel_]
ring = cc + (ring - cc) * (1 - E('CAP_IN', '0.015') / np.linalg.norm(ring - cc, axis=1))[:, None]
Vc = np.vstack([ring, cc]); Tc = [[NC, (j + 1) % NC, j] for j in range(NC)]
parts['cap'] = raw_mesh('cap', Vc, Tc); print('CAP ring', NC, 'centre', cc.round(3))
# ---- head (skull), cowl and necklace need the skull npz
skull = None
if SKULL != '-':
    S = np.load(SKULL); sc_, st_ = S['co'], S['tri']; eye_c = S['eye_c']; width = float(S['width'])
    EYES = co[np.isin(comp, [37, 38])]
    tgt_eye = np.array([0.0, EYES[:, 1].mean() + E('SKULL_DY', '0.0'), EYES[:, 2].mean() + E('SKULL_DZ', '0.0')])
    skk = E('SKULL_W', '0.140') / width
    sk = (sc_ - eye_c) * skk + tgt_eye
    parts['head'] = raw_mesh('head', sk, st_)
    print('SKULL scale', round(skk, 3), 'eye line', tgt_eye.round(3), 'bounds', sk.min(0).round(3), sk.max(0).round(3))
    # neck: a dark tube from inside the skull base (the foramen) down into the collar, behind the jaw (shadow inside the hood)
    cr = sk[S['label'] == 0]; back = cr[(np.abs(cr[:, 0]) < 0.02) & (cr[:, 1] > np.median(cr[:, 1]))]
    fm = back[np.argmin(back[:, 2])]; top = fm + np.array([0, E('NECK_TOP_DY', '-0.01'), 0.015])
    bot = np.array([0, MJ['FHP Neck'][1] + E('NECK_BOT_DY', '0.0'), MJ['FHP Neck'][2] - E('COWL_DOWN', '0.07')])
    print('NECK foramen', fm.round(3), 'bottom', bot.round(3))
    N = 12; V = []; T = []
    rings = [(top, E('COWL_R0', '0.024')), (0.5 * (top + bot), E('COWL_R1', '0.030')), (bot, E('COWL_R2', '0.045'))]
    for i, (c_, r) in enumerate(rings):
        for j in range(N):
            a_ = 2 * np.pi * j / N; V.append(c_ + [r * np.cos(a_), r * np.sin(a_), 0])
        if i:
            for j in range(N):
                a_, b_ = (i - 1) * N + j, (i - 1) * N + (j + 1) % N; T += [[a_, b_ + N, b_], [a_, a_ + N, b_ + N]]
    parts['cowl'] = raw_mesh('cowl', V, T)
    # necklace: fangs on a cord following the robe's neckline
    RV = np.vstack([verts(parts['robe']), verts(parts['hood'])]); ncx = 0.0; ncy = E('NK_CY', '-0.03')
    zf, zbk = E('NK_ZF', '0.40'), E('NK_ZB', '0.47'); pts = []; nrm = []
    angs = np.radians(np.linspace(-E('NK_SPAN', '100'), E('NK_SPAN', '100'), int(E('NK_N', '21'))))
    for a in angs:
        dirr = np.array([np.sin(a), -np.cos(a), 0.0]); z = zbk + (zf - zbk) * np.cos(a / 2) ** 2
        r0 = E('NK_RX', '0.11') * E('NK_RY', '0.12') / np.hypot(E('NK_RY', '0.12') * np.sin(a), E('NK_RX', '0.11') * np.cos(a))
        near = RV[np.abs(RV[:, 2] - z) < 0.015]; rel = near[:, :2] - [ncx, ncy]
        ang_n = np.arctan2(rel[:, 0], -rel[:, 1]); sel = np.abs((ang_n - a + np.pi) % (2 * np.pi) - np.pi) < 0.10
        rs = np.linalg.norm(rel[sel], axis=1); rs = rs[rs < r0 + 0.04]
        r = max(r0, (rs.max() if len(rs) else 0) + E('NK_OUT', '0.006'))
        pts.append([ncx + dirr[0] * r, ncy + dirr[1] * r, z]); nrm.append(dirr)
    pts = np.array(pts); nrm = np.array(nrm)
    V = []; T = []
    def cone(base, axis_, out_, L, R, n=5, bend=0.25):
        b0 = len(V); u = np.cross(axis_, out_); u /= np.linalg.norm(u); w = np.cross(u, axis_)
        segs = 3
        for s in range(segs + 1):
            f = s / segs; c = base + axis_ * L * f + out_ * (bend * L * f * f); rr_ = R * (1 - f) + 0.0004
            for j in range(n):
                a = 2 * np.pi * j / n; V.append(c + rr_ * (np.cos(a) * u + np.sin(a) * w))
        for s in range(segs):
            for j in range(n):
                a_, b_ = b0 + s * n + j, b0 + s * n + (j + 1) % n; T.extend([[a_, b_, b_ + n], [a_, b_ + n, a_ + n]])
        cap = len(V); V.append(base); [T.append([cap, b0 + (j + 1) % n, b0 + j]) for j in range(n)]
    for i, (p_, n_) in enumerate(zip(pts, nrm)):
        down = np.array([0, 0, -1.0]) * 0.75 + n_ * 0.35; down /= np.linalg.norm(down)
        L = E('FANG_L', '0.042') * (0.75 + 0.25 * np.cos(angs[i]))
        cone(p_, down, n_, L, E('FANG_R', '0.0055'))
    # cord: a thin tube through the fang bases
    n = 6; b0 = len(V)
    for i, p_ in enumerate(pts):
        tg = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; tg /= np.linalg.norm(tg); u = np.array([0, 0, 1.0]); w = np.cross(tg, u)
        for j in range(n):
            a = 2 * np.pi * j / n; V.append(p_ + 0.003 * (np.cos(a) * u + np.sin(a) * w))
    for i in range(len(pts) - 1):
        for j in range(n):
            a_, b_ = b0 + i * n + j, b0 + i * n + (j + 1) % n; T.extend([[a_, b_, b_ + n], [a_, b_ + n, a_ + n]])
    parts['necklace'] = raw_mesh('necklace', np.array(V), np.array(T))
    front = pts[np.argmin(np.abs(angs))]
    pend_at = front + np.array([0, -E('PEND_OUT', '0.018'), -E('PEND_DOWN', '0.050')])   # the pendant skull is added after the UVs (a copy of the head)
    print('NECKLACE fangs', len(pts), 'front', front.round(3))
# ---- reduce the robe and hood outside the borders
BUDGET = dict(robe=int(E('B_ROBE', '6000')), hood=int(E('B_HOOD', '1400')))


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
    md.use_symmetry = True; md.symmetry_axis = 'X'; md.vertex_group = 'free'; md.vertex_group_factor = 1.0
    bpy.ops.object.modifier_apply(modifier='d'); [o_.vertex_groups.remove(g_) for g_ in list(o_.vertex_groups)]; print('REDUCE', nm, t0_, '->', tris(o_))
names = list(parts); Co = []; Tr = []; Pa = []; Hp = []; Hl = []; base = 0
for k, nm in enumerate(names):
    if nm == 'hands':
        c, t = hc2, ht2; hpv = hp2
    else:
        c, t = arrays(parts[nm]); hpv = np.full(len(c), -100000)
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); Hp.append(hpv); Hl.append(S['label'] if nm == 'head' else np.full(len(c), -1)); base += len(c)
    print('PART', nm, len(c), len(t))
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names), hand_piece=np.concatenate(Hp), sh=sh, wr=wr, ax=ax,
         chains=json.dumps(CHAINS), carpal=np.array(CARPAL), arm_scale=S_ARM,
         head_label=np.concatenate(Hl), skull_k=skk if SKULL != '-' else 0, skull_eye=tgt_eye if SKULL != '-' else 0, pend_at=pend_at if SKULL != '-' else 0)
print('SAVED', base, sum(len(t) for t in Tr))
