"""Step A: the Meshy body on the MM9 bind pose (true handedness), from mm9_ghoul_claude/scripts/fit_ghoul.py.
Global fit (height without the tail, feet on MM9's floor), torso Kabsch on pelvis/shoulders/neck, each limb segment mapped
from its estimated joints onto MM9's (rotation + stretch along the bone), blended by diffused labels. The tail is laid
along MM9's tail chain by arc length (the arrowhead rigid past XtailE). Each digit of the right hand is laid along MM9's own
finger chain. The near (-x, the master's three-quarter side) half is kept and mirrored (MM9 is symmetric). Meshy's head
(in front of a plane through the neck) is removed: the head-only model replaces it (place_head.py).
Parts: 0 skin (main shell), 1 armour shells (gauntlets, greaves, belt), 2 small pieces (spikes, crest horns), 4 tail.
Args: <meshy glb> <work/mm9_true.npz> <config json> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Quaternion, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digits as DG, digits2 as D2
MESHY, MM9, CFG, OUT = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))
bpy.ops.wm.read_factory_settings(use_empty=True)
_d = np.load(MM9)
J = {str(k).replace('Bip01 ', ''): v for k, v in zip(_d['jn'], _d['jp'])}
A = _d['A']
bpy.ops.import_scene.gltf(filepath=MESHY)
body = next(o for o in bpy.data.objects if o.type == 'MESH')
Mw = body.matrix_world.copy(); body.parent = None; body.matrix_world = Mw; body.name = 'Body'
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o, do_unlink=True)
me = body.data
bpy.context.view_layer.objects.active = body; body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me.materials.clear()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
P0 = np.array([tuple(v.co) for v in me.vertices]); n = len(P0)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)


def global_fit(P, A):
    nt = P[:, 1] < np.percentile(P[:, 1], 5) + 0.62 * np.ptp(P[:, 1])
    at = A[:, 1] < 0.45
    s = np.ptp(A[at, 2]) / np.ptp(P[nt, 2])
    Q = P * s; dz = A[at, 2].min() - Q[nt, 2].min()
    zl, zh = -0.2, 0.5
    m = (Q[:, 2] + dz > zl) & (Q[:, 2] + dz < zh) & (np.abs(Q[:, 0]) < 0.25)
    ma = (A[:, 2] > zl) & (A[:, 2] < zh) & (np.abs(A[:, 0]) < 0.25)
    dy = 0.5 * (A[ma, 1].min() + A[ma, 1].max()) - 0.5 * (Q[m, 1].min() + Q[m, 1].max())
    dx = 0.5 * (A[:, 0].min() + A[:, 0].max()) - 0.5 * (Q[:, 0].min() + Q[:, 0].max())
    return s, np.array([dx, dy, dz])


def comps(mask):
    c = -np.ones(n, int); k = 0
    for i in np.nonzero(mask)[0]:
        if c[i] >= 0: continue
        st = [i]; c[i] = k
        while st:
            x = st.pop()
            for y in nbr[x]:
                if mask[y] and c[y] < 0: c[y] = k; st.append(y)
        k += 1
    return c, k


s_, t_ = global_fit(P0, A)
P = P0 * s_ + t_
print('GLOBAL scale', round(s_, 4), 't', t_.round(4))
comp, nc = comps(np.ones(n, bool)); sizes = np.bincount(comp); main = int(np.argmax(sizes))
PART = np.where(comp == main, 0, 1)
for c in range(nc):
    if c != main and sizes[c] < 150: PART[comp == c] = 2
# ---- head removal: Meshy's head (and its ram horns, eyes, teeth) in front of a plane through the neck
hp = np.array(cfg['head_plane_point']); hn = np.array(cfg['head_plane_normal']); hn = hn / np.linalg.norm(hn)
hb = cfg['head_box']
headside = ((P - hp) @ hn > 0) | ((P[:, 1] < hb[0]) & (P[:, 2] > hb[1]) & (np.abs(P[:, 0]) < hb[2]))
drop = np.zeros(n, bool)
for c in range(nc):
    m = comp == c
    if c != main:
        ctr = P[m].mean(0); ob = cfg['old_head_piece_box']
        if headside[m].mean() > 0.5 or (ctr[1] < ob[0] and ctr[2] > ob[1] and abs(ctr[0]) < ob[2]): drop[m] = True
HEADSIDE = headside & (comp == main)
# ---- tail: behind the buttocks, narrow, below the belt
tc = cfg['tail']
tail = (P[:, 1] > tc['y0']) & (np.abs(P[:, 0]) < tc['half_x']) & (P[:, 2] < tc['z_max'])
for c in range(nc):
    if c != main and tail[comp == c].mean() > 0.5: tail[comp == c] = True
PART[tail] = 4
print('PARTS', {int(k): int((PART == k).sum()) for k in np.unique(PART)}, 'comps', nc, 'dropped head', int(drop.sum()))
E = {k: np.array(v, float) for k, v in cfg['est'].items()}
for k in list(E):
    if k.startswith('R '):
        E['L ' + k[2:]] = E[k] * np.array([-1, 1, 1])


def refine(name, a, b):
    """bbox middle of the skin section through E[name], perpendicular to the a-b axis"""
    u = E[b] - E[a]; u = u / np.linalg.norm(u)
    q = P - E[name]; ax = q @ u; rad = np.linalg.norm(q - np.outer(ax, u), axis=1)
    m = (np.abs(ax) < 0.015) & (rad < cfg.get('refine_radius', 0.16)) & (PART != 4) & ~drop
    if m.sum() < 6: return
    c = 0.5 * (P[m].min(0) + P[m].max(0)); c = c - u * ((c - E[name]) @ u)
    print('REFINE', name, E[name].round(3), '->', c.round(3), 'n', int(m.sum()))
    E[name] = c


for s in 'RL':
    for nm, a, b in ((f'{s} Forearm', f'{s} UpperArm', f'{s} Hand'), (f'{s} Hand', f'{s} Forearm', f'{s} Knuckle'),
                     (f'{s} Calf', f'{s} Thigh', f'{s} Foot'), (f'{s} Foot', f'{s} Calf', f'{s} Toe')):
        if nm in cfg.get('refine', []) or nm.replace('L ', 'R ') in cfg.get('refine', []): refine(nm, a, b)


def rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(a @ b); sn = np.linalg.norm(v)
    if sn < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / sn ** 2)


def seg_map(ea, eb, ja, jb, name):
    u = eb - ea; L = np.linalg.norm(u); u = u / L
    k = np.linalg.norm(jb - ja) / L
    Rm = rot(u, jb - ja); S = np.eye(3) + (k - 1) * np.outer(u, u); A_ = Rm @ S
    print('SEG', name, 'stretch %.2f' % k, 'turn %.1f' % np.degrees(np.arccos(np.clip((jb - ja) @ u / np.linalg.norm(jb - ja), -1, 1))))
    return A_, ja - A_ @ ea


src = np.array([E['pelvis'], E['L UpperArm'], E['R UpperArm'], E['neck']]); dst = np.array([J['Pelvis'], J['L UpperArm'], J['R UpperArm'], J['Neck']])
sc, dc = src.mean(0), dst.mean(0)
H = (src - sc).T @ (dst - dc); U, _, Vt = np.linalg.svd(H); Rt = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
print('TORSO rot deg', round(np.degrees(np.arccos(min(1, (np.trace(Rt) - 1) / 2))), 2))
Tt = (Rt, dc - Rt @ sc)
SEGS, ends = {}, {}
for s in 'LR':
    hand_end = J[f'{s} Hand'] + (J[f'{s} Finger2'] - J[f'{s} Hand']) / np.linalg.norm(J[f'{s} Finger2'] - J[f'{s} Hand']) * np.linalg.norm(E[f'{s} Knuckle'] - E[f'{s} Hand'])
    toe_mm9 = J[f'{s} Toe11']
    for b, (ea, eb, ja, jb) in {f'{s} UpperArm': (f'{s} UpperArm', f'{s} Forearm', J[f'{s} UpperArm'], J[f'{s} Forearm']),
                                f'{s} Forearm': (f'{s} Forearm', f'{s} Hand', J[f'{s} Forearm'], J[f'{s} Hand']),
                                f'{s} Hand': (f'{s} Hand', f'{s} Knuckle', J[f'{s} Hand'], hand_end),
                                f'{s} Thigh': (f'{s} Thigh', f'{s} Calf', J[f'{s} Thigh'], J[f'{s} Calf']),
                                f'{s} Calf': (f'{s} Calf', f'{s} Foot', J[f'{s} Calf'], J[f'{s} Foot']),
                                f'{s} Foot': (f'{s} Foot', f'{s} Toe', J[f'{s} Foot'], toe_mm9)}.items():
        SEGS[b] = seg_map(E[ea], E[eb], ja, jb, b); ends[b] = (ea, eb)
names = list(SEGS)


def seg_d(Q, a, b):
    ab = b - a; t = (Q - a) @ ab / (ab @ ab); tc_ = np.clip(t, 0, 1)
    return np.linalg.norm(Q - a - np.outer(tc_, ab), axis=1), t


D = np.ones((n, len(names))) * 1e3
zh = 0.5 * (E['L Thigh'][2] + E['R Thigh'][2])
belt = cfg['belt_z']
for i, b in enumerate(names):
    d, t = seg_d(P, E[ends[b][0]], E[ends[b][1]])
    side = 1 if b[0] == 'L' else -1
    ok = (np.sign(P[:, 0]) == side) & (PART != 4) & ~drop
    if 'Thigh' in b or 'Calf' in b or 'Foot' in b:
        ok &= (P[:, 2] < belt) & (np.abs(P[:, 0]) < cfg['leg_max_x'])
        if 'Thigh' in b: ok &= (t > -0.1)
    else:
        ok &= ((P[:, 2] > belt) | (np.abs(P[:, 0]) > cfg['leg_max_x'])) & (np.abs(P[:, 0]) > cfg['arm_min_x'])
        if 'UpperArm' in b: ok &= t > -0.05
    if 'Hand' in b: d = np.where(t < 0, d + 0.02, d)
    D[:, i] = np.where(ok, d, 1e3)
best = D.argmin(1); dbest = D.min(1)
rad = cfg['radius']
free = np.array([dbest[i] < rad[names[best[i]].split()[1]] for i in range(n)])
lab = np.zeros((n, len(names) + 1)); lab[np.arange(n), np.where(free, best + 1, 0)] = 1
# whole small/armour pieces follow their majority label (a gauntlet must not tear between segments at its ends)
for c in range(nc):
    m = (comp == c) & (PART != 0) & (PART != 4)
    if m.sum() and c != main:
        pass
for _ in range(cfg.get('blend_iters', 8)):
    avg = np.array([lab[nb].mean(0) if nb else lab[i] for i, nb in enumerate(nbr)])
    lab = 0.5 * lab + 0.5 * avg
tw = np.clip((P[:, 2] - cfg['torso_blend'][0]) / (cfg['torso_blend'][1] - cfg['torso_blend'][0]), 0, 1); tw = tw * tw * (3 - 2 * tw)
Pel = J['Pelvis'] - E['pelvis']
base = (P @ Tt[0].T + Tt[1]) * tw[:, None] + (P + Pel) * (1 - tw[:, None])
Q = lab[:, :1] * base
for i, b in enumerate(names):
    A_, t2 = SEGS[b]; Q = Q + lab[:, i + 1:i + 2] * (P @ A_.T + t2)
# ---- tail: arc length along Meshy's straight tail onto MM9's chain; the arrowhead past tip_start stays rigid
tm = PART == 4
TP = P[tm]
b0 = np.array(tc['base']); u = TP[np.argmax((TP - b0) @ np.array(tc['dir']))] - b0; Lm = np.linalg.norm(u); u = u / Lm
chain = [J[k] for k in ('Xtailbase', 'Xtailpiv', 'XtailA', 'XtailB', 'XtailC', 'XtailD', 'XtailE')]
chain[0] = Pel + b0 if tc.get('base_from_meshy') else chain[0]
C9 = np.array(chain); L9 = np.r_[0, np.cumsum(np.linalg.norm(np.diff(C9, axis=0), axis=1))]
s_t = (TP - b0) @ u; off = TP - b0 - np.outer(s_t, u)
head0 = tc['tip_start'] * Lm                         # Meshy arc where the arrowhead begins
kk = L9[-1] / head0                                  # shaft arc -> MM9 chain arc
tipdir = (C9[-1] - C9[-2]) / np.linalg.norm(C9[-1] - C9[-2])
newT = np.zeros_like(TP)
for i, (s, o) in enumerate(zip(s_t, off)):
    if s < head0:
        a = max(s, 0) * kk; j = min(int(np.searchsorted(L9, a, side='right')) - 1, len(C9) - 2)
        tt = (C9[j + 1] - C9[j]); tt = tt / np.linalg.norm(tt)
        pt = C9[j] + tt * (a - L9[j]) + (min(s, 0) * u if s < 0 else 0)
        newT[i] = pt + rot(u, tt) @ o * tc['thick']
    else:
        newT[i] = C9[-1] + tipdir * (s - head0) * tc['tip_scale'] + rot(u, tipdir) @ o * tc['tip_scale']
# blend the tail root into the pelvis map over the first blend metres
wt = np.clip(s_t / tc['blend'], 0, 1)[:, None]; wt = wt * wt * (3 - 2 * wt)
Q[tm] = Q[tm] * (1 - wt) + newT * wt
print('TAIL verts', int(tm.sum()), 'meshy length', round(Lm, 3), 'mm9 chain', round(L9[-1], 3), 'shaft scale', round(kk, 3))
P = Q


# ---- right hand: palm swung onto MM9's palm, each digit laid along MM9's own chain
def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


root = J['R Hand']; fw = root - J['R Forearm']; fw = fw / np.linalg.norm(fw)
ax = (P - root) @ fw
near = np.linalg.norm(P - root, axis=1) < 0.55
for c in np.argsort(-sizes)[:30]:
    m = comp == c
    print('COMP', c, int(sizes[c]), 'part', int(PART[m][0]), 'drop', round(drop[m].mean(), 2), 'min', P[m].min(0).round(2), 'max', P[m].max(0).round(2))
print('NEAR HAND parts', {int(k): int((PART[near] == k).sum()) for k in np.unique(PART[near])}, 'comps', np.unique(comp[near]).tolist()[:20], 'sizes', [int(sizes[c]) for c in np.unique(comp[near])][:20])
cn = [c for c in np.unique(comp[near]) if c != main]
hc = max(cn, key=lambda c: int(((comp == c) & near).sum()))
region = comp == hc
seeds = [i for i in np.nonzero(region)[0] if ax[i] < ax[region].min() + 0.03]
d = DG.geodesic(P, nbr, seeds, region)
ids = np.nonzero(np.isfinite(d))[0]
br = D2.digit_tree(d, nbr, ids, cfg.get('digit_min', 0.05))
print('SEEDS', len(seeds), int(region.sum()), 'BRANCHES', [(round(b['base'], 3), round(b['tip'] - b['base'], 3), len(b['verts'])) for b in br])
loc = [i for i in ids if all(d[i] >= d[j] for j in nbr[i] if np.isfinite(d[j]))]
print('LOCALMAX', sorted([(round(float(d[i]), 3), P[i].round(3).tolist()) for i in loc], reverse=True)[:12])
# Meshy's fingers are fused (three geodesic tips for four digits), so they are rebuilt (make_digits.py): every branch
# and the palm past MM9's knuckle line are marked for deletion (digit 9)
DIG = np.full(n, -1)
for b in br: DIG[np.array(b['verts'])] = 9
kn = np.mean([J['R Finger1'], J['R Finger2'], J['R Finger3']], axis=0)
hd = kn - root; hd = hd / np.linalg.norm(hd)
DIG[region & ((P - kn) @ hd > cfg.get('knuckle_cut', 0.01))] = 9
th_ = br[int(np.argmin([b['base'] for b in br]))]
print('DELETE hand verts', int((DIG == 9).sum()), 'of', int(region.sum()))
DIG[region & (DIG != 9)] = 8                          # the kept palm (hole filling later)
print('floor', P[:, 2].min().round(3), 'bbox', P.min(0).round(3), P.max(0).round(3))
for v, p in zip(me.vertices, P): v.co = Vector(p)
for nm, arr in (('part', PART), ('drop', drop.astype(int)), ('digit', DIG), ('oldhead', HEADSIDE.astype(int))):
    a_ = me.attributes.new(nm, 'INT', 'POINT'); a_.data.foreach_set('value', arr.tolist())
me.update()
bm = bmesh.new(); bm.from_mesh(me)
dl = bm.verts.layers.int['drop']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[dl]], context='VERTS')
all_ = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=all_, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
# ---- digits: the fused Meshy fingers go, the palm is capped, and four tubes are built on MM9's own chains per hand
dg = bm.verts.layers.int['digit']; pl = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[dg] == 9], context='VERTS')
bnd = [e for e in bm.edges if e.is_boundary and all(v[dg] == 8 for v in e.verts)]
r_ = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
bmesh.ops.triangulate(bm, faces=r_['faces'])
print('PALM caps', len(r_['faces']), 'boundary edges', len(bnd))
DCF = cfg['digit_tubes']


def frame(t):
    a = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
    x = np.cross(t, a); x /= np.linalg.norm(x); return x, np.cross(t, x)


ntube = 0
for side in 'RL':
    for ci, f in enumerate('0123'):
        jt = [J[f'{side} Finger{f}'], J[f'{side} Finger{f}1'], J[f'{side} Finger{f}2']]
        u0 = (jt[1] - jt[0]) / np.linalg.norm(jt[1] - jt[0]); u2 = (jt[2] - jt[1]) / np.linalg.norm(jt[2] - jt[1])
        c = DCF['thumb'] if f == '0' else DCF['finger']
        tip = jt[2] + u2 * c['tip']
        knots = [jt[0] - u0 * c['root_in'], jt[0], jt[1], jt[2], tip]
        rads = [c['r0'] * 0.9, c['r0'], c['r1'], c['r2'], 0.0]
        pts, rs = [], []
        for k in range(4):
            sub = c.get('sub', 3) if k < 3 else c.get('claw_sub', 4)
            for i in range(sub):
                t = i / sub; pts.append(knots[k] * (1 - t) + knots[k + 1] * t)
                rk = rads[k] * (1 - t) + rads[k + 1] * t
                if k == 3: rk = rads[3] * (1 - t) ** c.get('claw_pow', 0.8)
                rs.append(rk * (1 + c.get('bulge', 0.1) * (i == 0 and 0 < k < 3)))
        pts.append(tip); rs.append(0.0)
        pts = np.array(pts); NS = c.get('sides', 8)
        rings = []
        xp = None
        for i, (p_, r) in enumerate(zip(pts, rs)):
            t = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]; t /= np.linalg.norm(t)
            if xp is None: x, y = frame(t)
            else:
                x = xp - t * (xp @ t); x /= np.linalg.norm(x); y = np.cross(t, x)
            xp = x
            if r <= 0:
                v = bm.verts.new(Vector(p_)); v[dg] = ci + (0 if side == 'R' else 10); v[pl] = 5; rings.append([v]); continue
            ring = []
            for a in range(NS):
                ang = 2 * np.pi * a / NS
                v = bm.verts.new(Vector(p_ + r * (np.cos(ang) * x + np.sin(ang) * y * c.get('flat', 0.85))))
                v[dg] = ci + (0 if side == 'R' else 10); v[pl] = 5; ring.append(v)
            rings.append(ring)
        cap = bm.verts.new(Vector(pts[0] - (pts[1] - pts[0]) * 0.3)); cap[dg] = ci + (0 if side == 'R' else 10); cap[pl] = 5
        for a in range(NS): bm.faces.new((cap, rings[0][(a + 1) % NS], rings[0][a]))
        for ra, rb in zip(rings[:-1], rings[1:]):
            for a in range(NS):
                if len(rb) == 1: bm.faces.new((ra[a], ra[(a + 1) % NS], rb[0]))
                else: bm.faces.new((ra[a], ra[(a + 1) % NS], rb[(a + 1) % NS], rb[a]))
        ntube += 1
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
print('TUBES', ntube)
bm.to_mesh(me); bm.free()
print('SYM verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
