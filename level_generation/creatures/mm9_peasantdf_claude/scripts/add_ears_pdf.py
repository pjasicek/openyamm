"""Modelled human ears for the dwarf women (job 7, user review 2026-11-04: "check if something can be done with their
ears"; the ear was a faint painted outline on a flat side of the head, Meshy's ear having been tucked flat by ear_tuck.py).

MM9's PeasantDF1-4 hair and hoods cover the ears; our hair/hood edge runs diagonally across the ear, so the ear is
modelled whole and tucked into the hair: its front (tragus, concha, helix root, lobe) shows in front of and below the
hair edge, the rest lies under the hair, and the hair/hood shell (with its back-side twin) is lifted over it where it
would not clear the ear by CLEAR (a smooth bump, as hair lies over an ear).

Each ear is one closed loose part on `Bip01 Head` (100 %, rigid with the head), built on a plane frame at the side of
the skull (e_out = +-x, e_up tilted TILT deg back, e_back): a 2D outline (cm, b back from the front attachment, u up from
the lobe) over a polar grid around the concha centre; the lateral surface stands h(rho, theta) cm off the skin (ray cast
along e_out onto the head's skin shell): plate lean, concha bowl down to the skin, antihelix ridge, scapha groove, rolled
helix rim, tragus, lobe; the medial surface is a coarser grid that runs from the rim back into the skull. The front
attachment (b < FRONT) and the lobe's front edge sink 1.2 mm into the skin, so the ear grows out of the cheek. Face
attributes: head = 1 (head set, HeadUV), ear = 1. HeadUV: lateral and medial islands of each ear in the head set's free
top strip at DENS px/cm (the face's density); the paint is ear_paint.py's (skin toned to the cheek, cavity shading).

Writes <out blend> and <out npz> (per ear vertex: rest position in the export frame (floor 0, glTF axes), HeadUV, normal,
ambient occlusion over the skin + ears + hair, rho, lateral flag, rim/lobe weight; triangles) for ear_paint.py.
Args: <in blend> <out blend> <out npz> [key=value ...] (SCALE 0.92, TILT 15, Y0 -0.044, Z0 0.395, CLEAR 0.3, DENS 22.5,
LEAN 0.34, UVX 0.06, UVY 0.86 = top-left of the island strip in UV)"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, NPZ = a[:3]
opt = dict(x.split('=', 1) for x in a[3:])
SCALE = float(opt.get('SCALE', 0.92)); TILT = math.radians(float(opt.get('TILT', 15)))
Y0 = float(opt.get('Y0', -0.044)); Z0 = float(opt.get('Z0', 0.395)); CLEAR = float(opt.get('CLEAR', 0.3))
DENS = float(opt.get('DENS', 22.5)); LEAN = float(opt.get('LEAN', 0.34)); FRONT = 0.45
UVX = float(opt.get('UVX', 0.06)); UVY = float(opt.get('UVY', 0.86))
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data; rig = ob.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
assert ob.matrix_world == ob.matrix_world.Diagonal((1, 1, 1, 1)) or True
M = ob.matrix_world; Mi = M.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh = bm.faces.layers.int['head']; lk = bm.faces.layers.int['hand']; lt = bm.faces.layers.int.get('twin')
le = bm.faces.layers.int.get('ear') or bm.faces.layers.int.new('ear')
assert not any(f[le] for f in bm.faces), 'ears already added'
# loose parts
comp = {}; parts = []
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = len(parts); cur = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = len(parts); st.append(o); cur.append(o)
    parts.append(cur)
big = max(range(len(parts)), key=lambda i: len(parts[i]))
W = lambda v: M @ v.co
hairp = [i for i in range(len(parts)) if i != big and len(parts[i]) > 300 and np.mean([W(v).z for v in parts[i]]) > 0.38]
print('EARS hair parts', [(i, len(parts[i])) for i in hairp])
skin_faces = [f for f in bm.faces if f[lh] and not f[lk] and not (lt and f[lt]) and comp[f.verts[0]] == big]
VW = [W(v) for v in bm.verts]
sk = BVHTree.FromPolygons(VW, [[v.index for v in f.verts] for f in skin_faces])
hair_faces = [f for f in bm.faces if comp[f.verts[0]] in hairp]
hb = BVHTree.FromPolygons(VW, [[v.index for v in f.verts] for f in hair_faces])

# ---- the outline (cm; b back from the front attachment, u up from the lobe), front-top first, clockwise seen from +x
OUT2 = np.array([(0.30, 4.60), (0.75, 5.45), (1.45, 5.95), (2.20, 5.90), (2.85, 5.40), (3.25, 4.55), (3.35, 3.60),
                 (3.15, 2.70), (2.75, 1.95), (2.35, 1.30), (2.00, 0.60), (1.60, 0.12), (1.05, 0.00), (0.62, 0.30),
                 (0.42, 0.95), (0.25, 1.60), (0.05, 2.25), (0.08, 3.00), (0.18, 3.80)])
C2 = np.array([1.05, 2.45])                    # concha centre
NA = 32


def outline(t):
    """Closed periodic Catmull-Rom through OUT2, t in [0, 1)."""
    n = len(OUT2); s = t * n; i = int(math.floor(s)) % n; f = s - math.floor(s)
    p0, p1, p2, p3 = OUT2[(i - 1) % n], OUT2[i], OUT2[(i + 1) % n], OUT2[(i + 2) % n]
    return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)


BND = np.array([outline(k / NA) for k in range(NA)])
RL = [0.0, 0.2, 0.36, 0.5, 0.62, 0.72, 0.8, 0.865, 0.92, 0.965]   # lateral rings (rim vertex at rho = 1 shared)
RM = [0.0, 0.5, 0.8, 0.93]                                          # medial rings


def bump(x, c, w):
    return math.exp(-((x - c) / w) ** 2)


def smooth(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0); return t * t * (3 - 2 * t)


def attach(k):
    """0..1: how much the outline point k is attached to the head (front edge, lobe front)."""
    b = BND[k][0]
    return 1.0 - smooth(FRONT - 0.15, FRONT + 0.25, b)


def lobe_w(p):
    return 1.0 - smooth(0.9, 1.7, p[1])


def h_lat(rho, k):
    """Lateral surface height (cm) over the skin at ring rho, angle index k."""
    p = C2 + rho * (BND[k] - C2)
    att = attach(k); lobe = lobe_w(p)
    base = 0.22 + LEAN * p[0]                                   # plate leaning out toward the back
    concha = (1 - smooth(0.25, 0.62, rho)) * (1 - 0.85 * lobe)  # bowl down to the skin around the centre
    h = base * (1 - concha) + 0.18 * concha - 0.06 * concha * bump(rho, 0.0, 0.18)   # floor >= 1.2 mm off the skin (no skin poking through)
    free = 1 - att
    h += free * (1 - lobe) * (0.20 * bump(rho, 0.66, 0.09) - 0.10 * bump(rho, 0.83, 0.05) + 0.16 * bump(rho, 0.95, 0.05))
    # tragus: a small flap in front of the concha
    h += 0.30 * bump(p[0], 0.25, 0.22) * bump(p[1], 2.25, 0.45) * (1 - smooth(0.7, 0.95, rho))
    # lobe: soft and thick, no relief
    h = h * (1 - 0.5 * lobe) + lobe * (0.40 + 0.18 * p[0]) * 0.5
    # attached rim sinks into the skin
    if rho > 0.85:
        h = h * (1 - att * smooth(0.85, 1.0, rho)) + (-0.12) * att * smooth(0.85, 1.0, rho)
    return h


def frame(sx):
    eo = Vector((sx, 0, 0)); eu = Vector((0, math.sin(TILT), math.cos(TILT))); eb = Vector((0, math.cos(TILT), -math.sin(TILT)))
    org = Vector((0, Y0, Z0))
    return eo, eu, eb, org


def place(sx, p2, h):
    """2D point (cm) and height (cm) -> world point; returns (point, skin point, hair distance from skin or None)."""
    eo, eu, eb, org = frame(sx)
    q = org + eb * (p2[0] * SCALE / 100) + eu * (p2[1] * SCALE / 100)
    hit = sk.ray_cast(q, eo, 0.16)          # from the head's mid-plane outward: the first skin hit is this side's
    s = hit[0] if hit[0] is not None else q + eo * 0.06
    hh = hb.ray_cast(s + eo * 1e-4, eo, 0.05)
    dh = (hh[0] - s).length * 100 if hh[0] is not None else None
    return s + eo * (h * SCALE / 100), s, dh


rep = {}
ears = []
for sx in (1, -1):
    V = []; meta = []          # (rho, lateral, rimw, lobe, b, u)
    idx_l = {}; idx_m = {}
    for ri, rho in enumerate(RL):
        for k in range(NA if rho > 0 else 1):
            p = C2 + rho * (BND[k] - C2)
            pt, s, dh = place(sx, p, h_lat(rho, k))
            idx_l[(ri, k)] = len(V); V.append([pt, s, dh, h_lat(rho, k)]); meta.append((rho, 1, smooth(0.86, 0.97, rho) * (1 - attach(k)), lobe_w(p), p[0], p[1]))
    rim = {}
    for k in range(NA):
        hl = h_lat(0.965, k); att = attach(k)
        h = hl - 0.12 * (1 - att) if att < 0.5 else -0.15
        pt, s, dh = place(sx, BND[k], h)
        rim[k] = len(V); V.append([pt, s, dh, h]); meta.append((1.0, 1, 1 - att, lobe_w(BND[k]), BND[k][0], BND[k][1]))
    for ri, rho in enumerate(RM):
        for k in range(NA if rho > 0 else 1):
            p = C2 + rho * (BND[k] - C2)
            if rho >= 0.93:
                h = h_lat(rho, k) - 0.26
            elif rho >= 0.8:
                h = min(h_lat(rho, k) - 0.3, 0.5 * h_lat(rho, k))
            else:
                h = -0.35
            if attach(k) > 0.5: h = min(h, -0.3)
            pt, s, dh = place(sx, p, h)
            idx_m[(ri, k)] = len(V); V.append([pt, s, dh, h]); meta.append((rho, 0, 0.0, lobe_w(p), p[0], p[1]))
    T = []
    TL = []                     # 1 = lateral island, 0 = medial

    def ring_faces(idx, rings, outer, lat):
        for ri in range(len(rings) - 1):
            for k in range(NA):
                k1 = (k + 1) % NA
                if ri == 0:
                    T.append((idx[(0, 0)], idx[(1, k)], idx[(1, k1)])); TL.append(lat)
                else:
                    a_, b_, c_, d_ = idx[(ri, k)], idx[(ri, k1)], idx[(ri + 1, k1)], idx[(ri + 1, k)]
                    T.append((a_, d_, c_)); T.append((a_, c_, b_)); TL.extend((lat, lat))
        last = len(rings) - 1
        for k in range(NA):
            k1 = (k + 1) % NA
            a_, b_ = idx[(last, k)], idx[(last, k1)]
            T.append((a_, outer[k], outer[k1])); T.append((a_, outer[k1], b_)); TL.extend((lat, lat))
    ring_faces(idx_l, RL, rim, 1); ring_faces(idx_m, RM, rim, 0)
    # tuck under the hair: report the clearance the hair needs over each lateral/rim vertex
    need = []
    for i, (pt, s, dh, h) in enumerate(V):
        if meta[i][1] and dh is not None and h > -0.05:
            need.append((s, dh, h * SCALE + CLEAR - dh))
    ears.append(dict(sx=sx, V=V, T=T, TL=TL, meta=meta, need=need))
    rep[sx] = {'verts': len(V), 'tris': len(T), 'under_hair': sum(1 for n in need), 'max_need_cm': round(max([n[2] for n in need] + [0]), 3)}
print('EARS plan', json.dumps(rep))

# ---- hair bump over the ears (hair/hood part and its back-side twin, same field)
hv = [v for i in hairp for v in parts[i]]
HP = np.array([tuple(W(v)) for v in hv])
disp = np.zeros(len(HP))
SIG = 0.009
for e in ears:
    sx = e['sx']
    for s, dh, nd in e['need']:
        if nd <= 0: continue
        top = np.array(tuple(s)) + np.array([sx, 0, 0]) * dh / 100
        r2 = ((HP - top) ** 2).sum(1)
        side = HP[:, 0] * sx > 0.02
        disp = np.where(side, np.maximum(disp, nd / 100 * np.exp(-r2 / (2 * SIG ** 2))), disp)
for v, dv, p in zip(hv, disp, HP):
    if dv > 1e-5:
        sx = 1 if p[0] > 0 else -1
        v.co = Mi @ (Vector(tuple(p)) + Vector((sx * dv, 0, 0)))
rep['hair_bump_max_cm'] = round(float(disp.max() * 100), 3); rep['hair_verts_moved'] = int((disp > 1e-4).sum())

# ---- add the ear geometry
gi = ob.vertex_groups['Bip01 Head'].index
dl = bm.verts.layers.deform.verify()
uvh = bm.loops.layers.uv['HeadUV']; uvb = bm.loops.layers.uv.get('UVMap')
# hair over and around the ears follows the head rigidly (it carried 14 % Neck and 12 % hair-chain weight there, so it
# swayed into the rigid ears by up to 9 mm in AttackMelee/Death): weights blended to 100 % Bip01 Head, fully within
# RIG_R0 of an ear vertex, fading out at RIG_R1
RIG_R0, RIG_R1 = float(opt.get('RIG_R0', 0.015)), float(opt.get('RIG_R1', 0.035))
EP = np.array([tuple(p) for e in ears for p, s, dh, h in e['V']])
from mathutils.kdtree import KDTree
kd = KDTree(len(EP))
for i, p in enumerate(EP): kd.insert(Vector(tuple(p)), i)
kd.balance()
nrig = 0
for v in hv:
    dist = kd.find(W(v))[2]
    f = 1 - min(max((dist - RIG_R0) / (RIG_R1 - RIG_R0), 0.0), 1.0)
    if f <= 0: continue
    old = dict(v[dl])
    for k in list(v[dl].keys()): v[dl][k] = old[k] * (1 - f)
    v[dl][gi] = v[dl].get(gi, 0.0) + f
    nrig += 1
rep['hair_verts_head_rigid'] = nrig
# island layout: per ear a lateral island (b, u plane) and a medial island, side by side in the top strip
SPAN_B, SPAN_U = 3.6 * SCALE, 6.2 * SCALE      # cm
pad = 14 / 2048
iw, ih = SPAN_B * DENS / 2048, SPAN_U * DENS / 2048
slots = {}
for n, key in enumerate([(1, 1), (1, 0), (-1, 1), (-1, 0)]):
    slots[key] = (UVX + n * (iw + pad), UVY)
rep['uv_islands'] = {f'{k[0]}_{"lat" if k[1] else "med"}': [round(x, 4) for x in (u0, v0, u0 + iw, v0 + ih)] for k, (u0, v0) in slots.items()}
assert UVX + 4 * (iw + pad) < 0.80 and UVY + ih < 0.995, 'ear islands leave the free strip'
out_np = {}
for e in ears:
    sx = e['sx']
    nv = [bm.verts.new(Mi @ pt) for pt, s, dh, h in e['V']]
    for v in nv:
        v[dl][gi] = 1.0
    nf = []
    for t, lat in zip(e['T'], e['TL']):
        try:
            f = bm.faces.new([nv[i] for i in t])
        except ValueError:
            continue
        f[lh] = 1; f[lk] = 0; f[le] = 1
        if lt: f[lt] = 0
        f.smooth = True
        f.material_index = 0
        nf.append((f, t, lat))
    bm.verts.index_update()
    for f, t, lat in nf:
        u0, v0 = slots[(sx, lat)]
        for L, i in zip(f.loops, t):
            b, u = e['meta'][i][4], e['meta'][i][5]
            uu = u0 + (b * SCALE + 0.15) * DENS / 2048 if sx > 0 else u0 + (SPAN_B - b * SCALE - 0.05) * DENS / 2048
            vv = v0 + (u * SCALE + 0.1) * DENS / 2048
            L[uvh].uv = (uu, vv)
            if uvb: L[uvb].uv = (uu, vv)
    e['nv'] = nv; e['nf'] = nf
bm.normal_update()
ear_faces = [f for e in ears for f, t, _ in e['nf']]
bmesh.ops.recalc_face_normals(bm, faces=ear_faces)
bm.normal_update()
# ambient occlusion per ear vertex (skin + ears + hair, rest pose), 48 hemisphere rays within 2.5 cm
allv = [W(v) for v in bm.verts]
polys = [[v.index for v in f.verts] for f in bm.faces if comp.get(f.verts[0], -1) in [big] + hairp or f[le]]
bvh = BVHTree.FromPolygons(allv, polys)
rng = np.random.default_rng(7)
D = rng.normal(size=(48, 3)); D /= np.linalg.norm(D, axis=1, keepdims=True)
for e in ears:
    ao = []; nrm = []; pos = []
    for v in e['nv']:
        n = (M.to_3x3() @ v.normal).normalized(); p = W(v)
        hits = 0; tot = 0
        for d in D:
            dv = Vector(d)
            if dv.dot(n) < 0: dv = -dv
            tot += dv.dot(n)
            h = bvh.ray_cast(p + n * 3e-4 + dv * 2e-4, dv, 0.025)
            if h[0] is not None: hits += dv.dot(n)
        ao.append(1 - hits / tot); nrm.append(tuple(n)); pos.append(tuple(p))
    e['ao'] = np.array(ao); e['nrm'] = np.array(nrm); e['pos'] = np.array(pos)
# export frame (glTF): x, y = z + lift, z = -y
LIFT = -min((M @ v.co).z for v in bm.verts if v.is_valid)    # build_export_v2.py's floor lift (lowest vertex to y = 0)
P_, N_, UV_, AO_, MT_, TR_, SIDE_ = [], [], [], [], [], [], []
off = 0
for e in ears:
    p = e['pos']; n = e['nrm']
    P_.append(np.stack([p[:, 0], p[:, 2] + LIFT, -p[:, 1]], 1)); N_.append(np.stack([n[:, 0], n[:, 2], -n[:, 1]], 1))
    AO_.append(e['ao']); MT_.append(np.array(e['meta'])); SIDE_.append(np.full(len(p), e['sx']))
    uv = np.zeros((len(p), 2))
    tri = []
    lat_t = []; tuv = []
    loc = {v: i for i, v in enumerate(e['nv'])}
    for f, t, lat in e['nf']:                            # loop order (recalc_face_normals may have flipped a face)
        tri.append([loc[L.vert] + off for L in f.loops]); lat_t.append(lat)
        tuv.append([tuple(L[uvh].uv) for L in f.loops])
    e['lat_t'] = lat_t; e['tuv'] = tuv
    UV_.append(uv); TR_.append(np.array(tri)); off += len(p)
np.savez(NPZ, tri_uv=np.concatenate([np.array(e['tuv']) for e in ears]), tri_lat=np.concatenate([e['lat_t'] for e in ears]), pos=np.concatenate(P_), nrm=np.concatenate(N_), uv=np.concatenate(UV_), ao=np.concatenate(AO_),
         meta=np.concatenate(MT_), tris=np.concatenate(TR_), side=np.concatenate(SIDE_),
         islands=np.array([list(slots[k]) + [iw, ih] for k in [(1, 1), (1, 0), (-1, 1), (-1, 0)]]))
bm.to_mesh(me); me.update()
rep['tris_total'] = sum(len(p.vertices) - 2 for p in me.polygons)
rep['ao_lat_p10_med'] = [round(float(np.percentile(np.concatenate(AO_), 10)), 3), round(float(np.median(np.concatenate(AO_))), 3)]
print('EARS', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
