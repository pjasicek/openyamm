"""Replace the Meshy body's weak head with the head-only Smart Topology model (from references_head/00) and loft the
neck from the body onto MM9's neck chain. Runs on the leg-fitted body (no weights yet; rig_chicken.py weights it).

Args: <fit blend (Body + MM9 meshes + MM9_Rig)> <head glb> <config json> <out blend> <report json>

1. Body: the old head out. A plane across the neck (normal = MM9's Xneck -> Xhead direction tilted by the config,
   through the point at CUT_H along that line from Xneck) cuts every body vertex inside a cylinder of CUT_R around the
   MM9 neck line; separate pieces in the cut-off part (the old eyes) go too.
2. New head (raw Meshy frame: beak toward -Y, crown +Z): the double-walled lining, if any, is removed (vertices that
   see no sky), holes closed (the beak stays shut), the shell decimated (symmetric collapse SKIN_RATIO) and its neck stub
   cut at raw z = HEAD_CUT_Z. Scaled to SCALE x MM9's head size (the MM9 Xhead/Xbeak vertices' extent along the beak),
   turned about X so its beak axis lies on MM9's (Xbeak -> MM9 beak tip: the beak points where MM9's does), placed so
   its beak root sits on MM9's Xbeak joint plus OFFSET.
3. A loft of LOFT rings bridges the body ring to the head's stub ring along a Hermite curve.
Face attribute 'part': 0 body, 1 head shell, 2 head small pieces (eyes), 3 loft. Vertex attribute 'piece' as the fit's
(2 for small separate pieces), 'chain' -1 for every new vertex. The bind beak tip is stored as Body['beak_tip'] and the
beak root as Body['beak_root'].
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, HEADGLB, CFGF, OUT, REP = a
cfg = json.load(open(CFGF))
CUT_H = cfg['cut_h']                      # along the MM9 neck line from Xneck (m)
CUT_TILT = math.radians(cfg.get('cut_tilt_deg', 0.0))   # plane normal tilted forward (+) about X
CUT_R = cfg.get('cut_r', 0.09)
HEAD_CUT_Z = cfg['head_cut_z']            # raw head frame
HEAD_TILT = math.radians(cfg.get('head_cut_tilt_deg', 0.0))   # the stub cut rises toward the nape
SCALE = cfg.get('scale', 1.0)
SKIN_RATIO = cfg.get('skin_ratio', 0.4)
LOFT = cfg.get('loft_rings', 4)
OFFSET = np.array(cfg.get('offset', [0, 0, 0]), float)
BEAK_FRAC = cfg.get('beak_frac', 0.3)     # beak region: within this share of the tip -> eye distance from the tip
rep = {'config': cfg}

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = bpy.data.objects['MM9_Rig']
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
mp, ml = [], []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        for v in o.data.vertices:
            if v.groups:
                g = max(v.groups, key=lambda g: g.weight)
                mp.append(tuple(o.matrix_world @ v.co)); ml.append(o.vertex_groups[g.group].name)
mp, ml = np.array(mp), np.array(ml)
sag = lambda d: math.atan2(d[2], -d[1])     # elevation of a forward (-Y) direction

# ---------------- MM9 head landmarks
bk9 = mp[np.isin(ml, ['Xbeak', 'beaknode'])]
tip9 = bk9[np.argmin(bk9[:, 1])]             # the forward-most beak vertex
axis9 = tip9 - J['Xbeak']
hd9 = mp[np.isin(ml, ['Xhead', 'Xbeak', 'beaknode'])]
len9 = float(hd9[:, 1].max() - hd9[:, 1].min())       # head length along y (MM9)
rep['mm9'] = {'tip': tip9.tolist(), 'beak_root': J['Xbeak'].tolist(), 'sag_deg': math.degrees(sag(axis9)),
              'head_len_y': len9, 'beak_len': float(np.linalg.norm(axis9))}

def components(bmx, verts=None):
    vs = verts if verts is not None else list(bmx.verts)
    allowed = set(vs); comp = {}
    for v in vs:
        if v in comp:
            continue
        c = len(set(comp.values())); st = [v]; comp[v] = c
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y in allowed and y not in comp:
                    comp[y] = c; st.append(y)
    return comp


# ---------------- 1. body: old head out
N0 = J['Xneck']
U = J['Xhead'] - J['Xneck']; U /= np.linalg.norm(U)
U = np.array(Matrix.Rotation(CUT_TILT, 3, 'X') @ Vector(U))
P0 = N0 + U * CUT_H
bm = bmesh.new(); bm.from_mesh(body.data)
bm.verts.layers.float.new('head_rz'); bm.verts.layers.float.new('head_ry')
pl = bm.verts.layers.int['piece']; cl = bm.verts.layers.int['chain']


CUT_YMAX = cfg.get('cut_ymax')


def in_cyl(co):
    d = np.array(co) - N0
    if CUT_YMAX is not None:
        return co[1] < CUT_YMAX
    return np.linalg.norm(d - (d @ U) * U) < CUT_R


ucoord = lambda co: float((np.array(co) - N0) @ U)
# old separate pieces in the head (eyes) go
old = [v for v in bm.verts if v[pl] != 0 and in_cyl(v.co) and ucoord(v.co) > CUT_H - 0.02]
rep['old_piece_verts'] = len(old)
old_eye = np.array([tuple(v.co) for v in old]).mean(0) if old else None
# the old head's width at eye level (the HD master's head proportions) sets the new head's scale
_hv = np.array([tuple(v.co) for v in bm.verts if v[pl] == 0 and in_cyl(v.co) and ucoord(v.co) > CUT_H])
old_w = float(np.ptp(_hv[np.abs(_hv[:, 2] - old_eye[2]) < 0.012, 0])) if old_eye is not None else None
rep['old_head'] = {'eye': None if old_eye is None else old_eye.tolist(), 'width_at_eye': old_w}
bmesh.ops.delete(bm, geom=old, context='VERTS')
# tiny loose bits of the Meshy body (under MIN_PIECE vertices) go
_bc = components(bm)
_bs = np.bincount(list(_bc.values()))
tiny = [v for v, c in _bc.items() if _bs[c] < cfg.get('min_piece', 40) and in_cyl(v.co) and ucoord(v.co) > CUT_H - 0.08]
rep['tiny_piece_verts'] = len(tiny)
bmesh.ops.delete(bm, geom=tiny, context='VERTS')
seed = [v for v in bm.verts if in_cyl(v.co) and ucoord(v.co) > CUT_H - 0.03]
sf = list({f for v in seed for f in v.link_faces}); se = list({e for f in sf for e in f.edges})
sv = list({x for f in sf for x in f.verts})
bmesh.ops.bisect_plane(bm, geom=sv + se + sf, dist=1e-6, plane_co=Vector(P0), plane_no=Vector(U), clear_outer=True)
comp = {}
for v in bm.verts:
    if v in comp:
        continue
    c = len(set(comp.values())); st = [v]; comp[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp:
                comp[y] = c; st.append(y)
# keep every component that still has body vertices outside the cut region (main body, wings, the other eye...)
cnt = np.bincount(list(comp.values()))
main = int(np.argmax(cnt))
stray = [v for v, c in comp.items() if c != main and v[pl] == 0]
rep['stray_verts'] = len(stray)
bmesh.ops.delete(bm, geom=stray, context='VERTS')
on = [e for e in bm.edges if e.is_boundary and all(abs(ucoord(x.co) - CUT_H) < 1e-4 for x in e.verts)]


def loops_of(edges):
    es = set(edges); seen = set(); out = []
    for e in edges:
        if e in seen:
            continue
        st, lp = [e], []; seen.add(e)
        while st:
            x = st.pop(); lp.append(x)
            for vv in x.verts:
                for y in vv.link_edges:
                    if y in es and y not in seen:
                        seen.add(y); st.append(y)
        out.append(lp)
    return out


def ordered(edges):
    adj = {}
    for e in edges:
        x, y = e.verts
        adj.setdefault(x, []).append(y); adj.setdefault(y, []).append(x)
    start = next(iter(adj)); out = [start]; prev = None; cur = start
    while True:
        nxt = [y for y in adj[cur] if y is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]; out.append(cur)
    return out


bl = loops_of(on)
ring_b_edges = max(bl, key=len)
ring_b = ordered(ring_b_edges)
RB = np.array([tuple(v.co) for v in ring_b])
cb = RB.mean(0)
rep['body_ring'] = {'verts': len(ring_b), 'loops': len(bl), 'centre': cb.round(4).tolist(),
                    'half_width': float(np.abs(RB[:, 0] - cb[0]).max())}

# ---------------- 2. new head (raw)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HEADGLB)
new = [o for o in bpy.data.objects if o not in before]
hsrc = next(o for o in new if o.type == 'MESH')
hb = bmesh.new(); hb.from_mesh(hsrc.data); hb.transform(hsrc.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(hb, verts=hb.verts, dist=1e-6)
kind = hb.verts.layers.int.new('kind')


def components(bmx, verts=None):
    vs = verts if verts is not None else list(bmx.verts)
    allowed = set(vs); comp = {}
    for v in vs:
        if v in comp:
            continue
        c = len(set(comp.values())); st = [v]; comp[v] = c
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y in allowed and y not in comp:
                    comp[y] = c; st.append(y)
    return comp


hc = components(hb)
hsz = np.bincount(list(hc.values()))
shell_c = int(np.argmax(hsz))
for v in hb.verts:
    v[kind] = 1 if hc[v] == shell_c else 2
rep['head_raw'] = {'verts': len(hb.verts), 'components': sorted(hsz.tolist(), reverse=True)[:12]}
# lining: shell vertices that see no sky (a large connected sheet only)
hb.normal_update()
bvh = BVHTree.FromBMesh(hb)
rng = np.random.default_rng(0)
DIRS = rng.normal(size=(48, 3)); DIRS /= np.linalg.norm(DIRS, axis=1)[:, None]
inner = []
for v in hb.verts:
    if v[kind] != 1:
        continue
    nrm = np.array(v.normal); hit = tot = 0
    for d in DIRS:
        if d @ nrm <= 0.05:
            continue
        tot += 1
        if bvh.ray_cast(v.co + Vector(d) * 1e-4, Vector(d), 5.0)[0] is not None:
            hit += 1
    if tot and (tot - hit) / tot < 0.02:
        inner.append(v)
ic = components(hb, inner)
isz = np.bincount(list(ic.values())) if ic else np.zeros(0, int)
inner = [v for v in inner if isz[ic[v]] >= 200] if cfg.get('remove_lining') else []
rep['head_raw']['lining_verts'] = len(inner)
bmesh.ops.delete(hb, geom=inner, context='VERTS')
hc = components(hb, [v for v in hb.verts if v[kind] == 1])
hsz = np.bincount(list(hc.values()))
bmesh.ops.delete(hb, geom=[v for v, c in hc.items() if c != int(np.argmax(hsz))], context='VERTS')
holes = [e for e in hb.edges if e.is_boundary]
if holes:
    f = bmesh.ops.holes_fill(hb, edges=holes, sides=0)
    bmesh.ops.triangulate(hb, faces=f['faces'])
rep['head_raw']['holes_filled_edges'] = len(holes)
# the eyes: the two small pieces nearest the head's side surface (or none)
small = {}
for v in hb.verts:
    if v[kind] == 2:
        small.setdefault(id(v), v)
# decimate the shell symmetrically
tmp = hb.copy(); kl = tmp.verts.layers.int['kind']
bmesh.ops.delete(tmp, geom=[v for v in tmp.verts if v[kl] != 1], context='VERTS')
m_sh = bpy.data.meshes.new('HeadShell'); tmp.to_mesh(m_sh); tmp.free()
o_sh = bpy.data.objects.new('HeadShell', m_sh); sc.collection.objects.link(o_sh)
if SKIN_RATIO < 0.999:
    md = o_sh.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = SKIN_RATIO
    md.use_symmetry = True; md.symmetry_axis = 'X'
    for o in bpy.data.objects:
        o.select_set(o == o_sh)
    bpy.context.view_layer.objects.active = o_sh
    bpy.ops.object.modifier_apply(modifier=md.name)
eb = hb.copy(); kl = eb.verts.layers.int['kind']
bmesh.ops.delete(eb, geom=[v for v in eb.verts if v[kl] != 2], context='VERTS')
m_ey = bpy.data.meshes.new('HeadEyes'); eb.to_mesh(m_ey); eb.free(); hb.free()
nb = bmesh.new(); nb.from_mesh(m_sh)
kl = nb.verts.layers.int.get('kind') or nb.verts.layers.int.new('kind')
for v in nb.verts:
    v[kl] = 1
nsh = len(nb.verts)
nb.from_mesh(m_ey)
nb.verts.ensure_lookup_table()
for v in nb.verts[nsh:]:
    v[kl] = 2
bpy.data.objects.remove(o_sh)
# stub cut (raw z plane)
shell = [v for v in nb.verts if v[kl] == 1]
sf = list({f for v in shell for f in v.link_faces}); se = list({e for f in sf for e in f.edges})
HN = np.array([0.0, -math.sin(HEAD_TILT), math.cos(HEAD_TILT)])    # plane normal (toward the head)
hcut = lambda co: float((np.array(co) - np.array([0, 0, HEAD_CUT_Z])) @ HN)
bmesh.ops.bisect_plane(nb, geom=shell + se + sf, dist=1e-6, plane_co=(0, 0, HEAD_CUT_Z), plane_no=Vector(-HN),
                       clear_outer=True)
hc = components(nb, [v for v in nb.verts if v[kl] == 1])
hsz = np.bincount(list(hc.values()))
bmesh.ops.delete(nb, geom=[v for v, c in hc.items() if c != int(np.argmax(hsz))], context='VERTS')
_pc = components(nb, [v for v in nb.verts if v[kl] == 2])
_low = [c for c in set(_pc.values()) if max(hcut(v.co) for v, cc in _pc.items() if cc == c) < 0]
bmesh.ops.delete(nb, geom=[v for v, cc in _pc.items() if cc in _low], context='VERTS')
hon = [e for e in nb.edges if e.is_boundary and all(abs(hcut(x.co)) < 1e-4 for x in e.verts)]
hl = loops_of(hon)
ring_h_edges = max(hl, key=len)
ring_h = ordered(ring_h_edges)
rep['head_ring_loops'] = len(hl)
rep['head_open_edges_other'] = sum(1 for e in nb.edges if e.is_boundary) - len(ring_h_edges)
# raw landmarks: beak tip (forward-most shell vertex), eyes (small pieces' centre, else the widest point), beak root
SH = np.array([tuple(v.co) for v in nb.verts if v[kl] == 1])
tip_raw = SH[np.argmin(SH[:, 1])]
# eyes: the mirror pair of small pieces off the midline with the highest centres (not the comb on the midline, the
# wattles, earlobes or nostril plates lower down)
_ec = components(nb, [v for v in nb.verts if v[kl] == 2])
_cent = {}
for v, c in _ec.items():
    _cent.setdefault(c, []).append(tuple(v.co))
_cent = {c: np.array(p).mean(0) for c, p in _cent.items()}
_side = sorted([c for c, m in _cent.items() if abs(m[0]) > 0.03], key=lambda c: -_cent[c][2])[:2]
eye_raw = np.mean([_cent[c] for c in _side], 0) if len(_side) == 2 else None
rep['head_raw']['small_pieces'] = {int(c): np.round(m, 3).tolist() for c, m in _cent.items()}
if eye_raw is None or abs(eye_raw[0]) > 0.01:
    eye_raw = np.array([0.0, tip_raw[1] + 0.35 * np.ptp(SH[:, 1]), tip_raw[2]])
eye_raw[0] = 0.0
skull = SH[SH[:, 2] > eye_raw[2] - 0.1]
back_raw = float(skull[:, 1].max())
root_raw = np.array([0.0, tip_raw[1] + 0.4 * (eye_raw[1] - tip_raw[1]), tip_raw[2] + 0.4 * (eye_raw[2] - tip_raw[2])])
rep['head_raw'].update({'width_at_eye': float(np.ptp(SH[np.abs(SH[:, 2] - eye_raw[2]) < 0.09, 0])), 'tip': tip_raw.round(4).tolist(), 'eye': eye_raw.round(4).tolist(), 'skull_back_y': back_raw,
                        'eye_tip_sag_deg': math.degrees(sag(tip_raw - eye_raw))})
# placement: skull length (beak tip -> back of the skull at eye height) = SCALE x MM9's head length; turned about X
# so the eye -> beak tip line has MM9's Xhead -> beak tip elevation; the beak tip on MM9's beak tip (+ OFFSET)
new_w = float(np.ptp(SH[np.abs(SH[:, 2] - eye_raw[2]) < 0.012 / 0.13, 0]))
s = SCALE * (old_w / new_w if old_w else len9 / (back_raw - tip_raw[1]))
ref9 = tip9 - J['Xhead']
alpha = sag(tip_raw - eye_raw) - sag(ref9)
R = np.array(Matrix.Rotation(alpha, 3, 'X'))
E9 = J['Xhead'] + cfg.get('eye_frac', 0.45) * (J['Xbeak'] - J['Xhead'])
T = E9 + OFFSET - s * (R @ eye_raw)
place = lambda p: s * (R @ np.array(p)) + T
for v in nb.verts:
    v.co = Vector(place(tuple(v.co)))
tip_b, root_b = place(tip_raw), place(root_raw)
RH = np.array([tuple(v.co) for v in ring_h])
ch = RH.mean(0)
rep['placement'] = {'scale': s, 'turn_deg': math.degrees(alpha), 'beak_tip': tip_b.round(4).tolist(),
                    'beak_root': root_b.round(4).tolist(), 'head_ring_centre': ch.round(4).tolist(),
                    'head_ring_half_width': float(np.abs(RH[:, 0] - ch[0]).max()), 'gap': float(np.linalg.norm(ch - cb)),
                    'eye': place(eye_raw).round(4).tolist(), 'xhead': J['Xhead'].round(4).tolist()}

# ---------------- 3. loft (body ring copy -> rings -> bridge to the head ring)
n_b = U
n_h = R @ HN                               # the stub cut's normal (into the head)
up_b = np.array([0, -1.0, 0]) - (np.array([0, -1.0, 0]) @ n_b) * n_b; up_b /= np.linalg.norm(up_b)   # forward
up_h = R @ np.array([0, -1.0, 0]); up_h -= (up_h @ n_h) * n_h; up_h /= np.linalg.norm(up_h)


def ang(P, c, up, n):
    side = np.cross(n, up)
    d = P - c
    return np.arctan2(d @ side, d @ up), d @ up, d @ side


th_b, ab, bb = ang(RB, cb, up_b, n_b)
th_h, ah, bh = ang(RH, ch, up_h, n_h)
oh = np.argsort(th_h)
ts = np.concatenate([th_h[oh] - 2 * np.pi, th_h[oh], th_h[oh] + 2 * np.pi])
ah_i = np.interp(th_b, ts, np.tile(ah[oh], 3)); bh_i = np.interp(th_b, ts, np.tile(bh[oh], 3))
L = float(np.linalg.norm(ch - cb))


def herm(t):
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * cb + h10 * n_b * L + h01 * ch + h11 * n_h * L


# body tangents: each ring vertex continues the body surface below the cut (G1 at the seam)
low = np.array([tuple(v.co) for v in bm.verts if v[pl] == 0 and in_cyl(v.co) and CUT_H - 0.03 < ucoord(v.co) < CUT_H - 0.008])
th_low, _, _ = ang(low, cb, up_b, n_b) if len(low) else (None, None, None)
TB = []
for j in range(len(RB)):
    if th_low is None:
        TB.append(n_b); continue
    dth = np.abs((th_low - th_b[j] + np.pi) % (2 * np.pi) - np.pi)
    cand = np.argsort(dth)[:3]
    q = low[cand].mean(0)
    t_ = RB[j] - q; t_ /= np.linalg.norm(t_)
    t_ = 0.5 * t_ + 0.5 * n_b; t_ /= np.linalg.norm(t_)
    TB.append(t_)
TB = np.array(TB)
for _ in range(4):                     # smooth the tangents along the ring
    TB = 0.5 * TB + 0.25 * (np.roll(TB, 1, 0) + np.roll(TB, -1, 0))
TB /= np.linalg.norm(TB, axis=1)[:, None]
side_h = np.cross(n_h, up_h)
HJ = ch + ah_i[:, None] * up_h + bh_i[:, None] * side_h
rep['loft_tangent_dev_deg'] = float(np.degrees(np.arccos(np.clip(TB @ n_b, -1, 1))).max())


def herm_col(j, t):
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * RB[j] + h10 * TB[j] * L + h01 * HJ[j] + h11 * n_h * L


ring_copy = [nb.verts.new(Vector(p)) for p in RB]
for v in ring_copy:
    v[kl] = 3
n = len(RB)
rings = [ring_copy]
q_bh = Vector(n_b).rotation_difference(Vector(n_h))
for k in range(1, LOFT + 1):
    t = k / (LOFT + 1)
    n_t = np.array(Quaternion().slerp(q_bh, t) @ Vector(n_b))
    up_t = (1 - t) * up_b + t * up_h; up_t -= (up_t @ n_t) * n_t; up_t /= np.linalg.norm(up_t)
    side_t = np.cross(n_t, up_t)
    C = herm(t)
    Q = np.array([herm_col(j, t) for j in range(n)])
    # low-pass the ring around the neck (a notch in either end ring would run down the loft as a pleat); the end
    # rings stay exact, the inner rings smooth most in the middle
    lam = cfg.get('loft_smooth', 0.5) * math.sin(math.pi * t)
    for _ in range(cfg.get('loft_smooth_iters', 6)):
        Q = (1 - lam) * Q + lam * 0.5 * (np.roll(Q, 1, 0) + np.roll(Q, -1, 0))
    ring = [nb.verts.new(Vector(q)) for q in Q]
    for v in ring:
        v[kl] = 4
    rings.append(ring)
for r0, r1 in zip(rings, rings[1:]):
    for j in range(n):
        nb.faces.new((r0[j], r0[(j + 1) % n], r1[(j + 1) % n], r1[j]))
last = [nb.edges.get((rings[-1][j], rings[-1][(j + 1) % n])) or nb.edges.new((rings[-1][j], rings[-1][(j + 1) % n]))
        for j in range(n)]
res = bmesh.ops.bridge_loops(nb, edges=last + ring_h_edges)
rep['loft'] = {'rings': LOFT, 'ring_verts': n, 'head_ring_verts': len(ring_h), 'bridge_faces': len(res['faces'])}
bmesh.ops.triangulate(nb, faces=list(nb.faces))

# ---------------- 4. join: head part into the body; the ring copy welds onto the body ring
hm = bpy.data.meshes.new('HeadPart'); nb.to_mesh(hm); nb.free()
kv = np.zeros(len(hm.vertices), np.int32); hm.attributes['kind'].data.foreach_get('value', kv)
bm.verts.ensure_lookup_table()
part_b = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
for f in bm.faces:
    f[part_b] = 0
rz = bm.verts.layers.float['head_rz']
ry = bm.verts.layers.float['head_ry']
for v in bm.verts:
    v[rz] = -9.0; v[ry] = 9.0
unplace = lambda p: R.T @ ((np.array(p) - T) / s)
newv = []
for i, v in enumerate(hm.vertices):
    x = bm.verts.new(v.co)
    x[pl] = 2 if kv[i] == 2 else 0
    x[cl] = -1
    if kv[i] in (1, 2):
        r_ = unplace(tuple(v.co)); x[rz] = float(r_[2]); x[ry] = float(r_[1])
    else:
        x[rz] = -5.0; x[ry] = 5.0      # loft: below the stub
    newv.append(x)
dup_faces = 0
for p in hm.polygons:
    ks = [kv[i] for i in p.vertices]
    try:
        f = bm.faces.new([newv[i] for i in p.vertices])
    except ValueError:
        dup_faces += 1
        continue
    f[part_b] = 2 if all(k == 2 for k in ks) else 3 if any(k in (3, 4) for k in ks) else 1
# weld the ring copy (kind 3) onto the body ring by position
targetmap = {}
for i, v in enumerate(hm.vertices):
    if kv[i] == 3:
        j = int(np.argmin(np.linalg.norm(RB - np.array(v.co), axis=1)))
        targetmap[newv[i]] = ring_b[j]
bmesh.ops.weld_verts(bm, targetmap=targetmap)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons:
    p.use_smooth = True
body['beak_tip'] = list(tip_b)
body['beak_root'] = list(root_b)
body['head_raw'] = json.dumps({'cut_z': HEAD_CUT_Z, 'tip': tip_raw.tolist(), 'eye': eye_raw.tolist(), 'root': root_raw.tolist()})
rep['dup_faces_skipped'] = dup_faces
rep['result'] = {'verts': len(body.data.vertices), 'tris': sum(len(p.vertices) - 2 for p in body.data.polygons)}
bmc = bmesh.new(); bmc.from_mesh(body.data)
rep['result']['open_edges'] = sum(1 for e in bmc.edges if e.is_boundary)
rep['result']['nonmanifold_edges'] = sum(1 for e in bmc.edges if len(e.link_faces) > 2)
bmc.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=float)
print('GRAFT ' + json.dumps(rep, default=float))
