"""Procedural left wing for the MM7 Dragon v2 (system Python): arm, leading finger, two trailing fingers, thumb and
finger claws, and a double-layer membrane with scalloped trailing edges, in the flight rest pose.

Why: the Meshy wing was frontal (membrane facing forward, so it could not reproduce the native flight silhouettes),
ragged (strips, notches, doubled membrane) and its retexture blotchy. The native planform is read from the restored
m182sa2 frame, where the raised wing is seen broadside (README "v2 wing"): wrist ahead of the shoulder with an ivory
thumb claw, a long swept leading finger, a second finger running straight back, a third from the elbow, scallops
between the tips and the membrane root along the back.

Wing frame: u outward (span), v backward (+Y), n = u x v (up). Rest: plane through the shoulder joint, raised by
REST_ELEVATION about +Y. The membrane is two layers 1.2 mm apart, joined by a rim (a closed thin shell; the engine
culls back faces); its root band is pulled onto the body surface (scripts/shoulder_envelope.py). Bone tubes are
8-sided generalised cylinders; claws are curved cones. UVs: membrane planar (both layers share it, so the two sides
show the same paint), tubes unrolled, claws in one shared ivory patch. Weights are analytic (inverse distance to the
wing bones in the wing plane; tubes and claws rigid with blended joints).
Writes work/v2/wing_left.npz. Usage: build_wing.py <shoulder_env.npz>"""
import json, sys
import numpy as np
from pathlib import Path
from scipy.spatial import Delaunay, cKDTree
from scipy.ndimage import map_coordinates

P = Path(__file__).resolve().parents[1]; OUT = P / 'work/v2'
REST_ELEVATION = np.radians(10.)
JOINT = np.array([.050, -.268, .300])                      # shoulder joint (inside the body)
# planform (metres, wing frame) from m182sa2, scaled by the body length (README "v2 wing")
# measured on m182sa2 (2.2 mm per x2 pixel): shoulder (300,240), elbow (300,200), wrist (320,150), tips (147,10),
# (130,131), (190,257); the third tip is moved out to u = 0.06 so the horizontal rest wing clears the back
S = np.array([0., 0.]); E = np.array([.088, .020]); W = np.array([.198, -.044])
T1 = np.array([.506, .337]); T2 = np.array([.255, .374]); T3 = np.array([.060, .280]); R = np.array([.000, .100])
M1 = W + .45 * (T1 - W) + .018 * np.array([.68, -.73])    # leading finger knuckle, bowed toward the leading edge
SAG = {'T1T2': .060, 'T2T3': .070, 'T3R': .035}
THICK = .0006                                               # half the membrane thickness
U = np.array([np.cos(REST_ELEVATION), 0., np.sin(REST_ELEVATION)]); V = np.array([0., 1., 0.]); N = np.cross(U, V)

def bezier(a, b, sag, n):
    m = (a + b) / 2; d = b - a; inward = np.array([-d[1], d[0]]) / np.linalg.norm(d)   # left of a->b (CCW outline)
    c = m + sag * inward; t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b

def polyline(points, step):
    pts = [points[0]]
    for a, b in zip(points[:-1], points[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        pts += [a + (b - a) * k / n for k in range(1, n + 1)]
    return np.array(pts)

def resample(curve, step):
    seg = np.linalg.norm(np.diff(curve, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    n = max(2, int(np.ceil(s[-1] / step)) + 1); t = np.linspace(0, s[-1], n)
    return np.c_[np.interp(t, s, curve[:, 0]), np.interp(t, s, curve[:, 1])]

# ---------------------------------------------------------------- membrane outline (counter-clockwise below)
lead = resample(np.r_[polyline([S, E, W], .004), polyline([W, M1, T1], .004)[1:]], .016)
free1 = resample(bezier(T1, T2, SAG['T1T2'], 80), .008)
free2 = resample(bezier(T2, T3, SAG['T2T3'], 80), .008)
free3 = resample(bezier(T3, R, SAG['T3R'], 60), .008)
root = resample(polyline([R, S], .01), .016)
outline = np.r_[lead[:-1], free1[:-1], free2[:-1], free3[:-1], root[:-1]]
kind_edge = np.r_[np.full(len(lead) - 1, 1), np.full(len(free1) - 1, 0), np.full(len(free2) - 1, 0), np.full(len(free3) - 1, 0),
                  np.full(len(root) - 1, 2)]          # 1 bone-embedded, 0 free (scallop), 2 root (body)
area = .5 * np.sum(outline[:, 0] * np.roll(outline[:, 1], -1) - np.roll(outline[:, 0], -1) * outline[:, 1])
if area < 0: outline = outline[::-1]; kind_edge = kind_edge[::-1]

def inside(p, poly=outline):
    x, y = p[:, 0], p[:, 1]; res = np.zeros(len(p), bool); j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        c = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-18) + xi)
        res ^= c; j = i
    return res

ribs = {'F2': resample(polyline([W, T2], .01), .020), 'F3': resample(polyline([E, T3], .01), .020)}
spacing = .022
gx, gy = np.meshgrid(np.arange(-.05, .56, spacing), np.arange(-.06, .45, spacing * .866))
gx = gx + (np.arange(gx.shape[0])[:, None] % 2) * spacing / 2
grid = np.c_[gx.ravel(), gy.ravel()]
grid = grid[inside(grid)]
interior_lines = np.r_[ribs['F2'][1:-1], ribs['F3'][1:-1]]
bt = cKDTree(np.r_[outline, interior_lines]); d, _ = bt.query(grid); grid = grid[d > .011]
pts2 = np.r_[outline, interior_lines, grid]
nb = len(outline)
tri = Delaunay(pts2).simplices
cent = pts2[tri].mean(1); tri = tri[inside(cent)]
# drop slivers on the outline (Delaunay may bridge concave scallops)
cross2 = lambda a, b: a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
a2 = np.abs(cross2(pts2[tri[:, 1]] - pts2[tri[:, 0]], pts2[tri[:, 2]] - pts2[tri[:, 0]])) / 2
tri = tri[a2 > 1e-8]
# orient counter-clockwise in (u, v) => normal +n
cr = cross2(pts2[tri[:, 1]] - pts2[tri[:, 0]], pts2[tri[:, 2]] - pts2[tri[:, 0]]); tri[cr < 0] = tri[cr < 0][:, [0, 2, 1]]

# ---------------------------------------------------------------- bone segments (for weights and tubes)
BONES = {'Wing0': (S, E), 'Wing1': (E, W), 'Wing2': (W, M1), 'Wing3': (M1, T1), 'WingF2': (W, T2), 'WingF3': (E, T3)}
def seg_dist(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1); return np.linalg.norm(p - a - t[:, None] * d, axis=1), t

def membrane_weights(p):
    """Wing bones by inverse distance (power 4) among themselves; the body takes over toward the root line through a
    smooth band 80 mm wide (Spine2 at the shoulder, Spine1 toward R), so a stroke spreads the root stretch over the
    inner panel instead of one row of triangles."""
    names = list(BONES) + ['Spine2', 'Spine1']
    D = np.array([seg_dist(p, *BONES[n])[0] for n in BONES]).T; wb = 1 / (D + .012) ** 4
    keep = np.argsort(-wb, 1)[:, :3]; ww = np.zeros_like(wb); np.put_along_axis(ww, keep, np.take_along_axis(wb, keep, 1), 1)
    ww /= ww.sum(1, keepdims=True)
    dr, tr = seg_dist(p, S, R); rho = np.clip(1 - dr / .08, 0, 1); rho = rho * rho * (3 - 2 * rho)
    # the arm itself never follows the body: within 25 mm of the arm the band fades out
    da = np.minimum(seg_dist(p, S, E)[0], seg_dist(p, E, W)[0]); rho *= np.clip(da / .025, 0, 1)
    out = np.c_[ww * (1 - rho[:, None]), rho * (1 - tr), rho * tr]
    out[out < 1e-3] = 0
    keep = np.argsort(-out, 1)[:, :4]; o2 = np.zeros_like(out); np.put_along_axis(o2, keep, np.take_along_axis(out, keep, 1), 1); out = o2
    out /= out.sum(1, keepdims=True); return names, out

# ---------------------------------------------------------------- body surface for the root band
E_ = np.load(sys.argv[1]); ys_, zs_, env = E_['ys'], E_['zs'], E_['env']
def body_x(y, z):
    return map_coordinates(env, [(y - ys_[0]) / (ys_[1] - ys_[0]), (z - zs_[0]) / (zs_[1] - zs_[0])], order=1, mode='nearest')

def to3d(p2, h=0.):
    return JOINT + p2[:, :1] * U + p2[:, 1:2] * V + np.atleast_1d(h)[:, None] * N

# billow: up to 9 mm between ribs, zero on bones, root and free edges
lines = [polyline([S, E, W], .004), polyline([W, M1, T1], .004), ribs['F2'], ribs['F3'], polyline([R, S], .004)]
dl = cKDTree(np.concatenate(lines)).query(pts2)[0]
de = cKDTree(np.r_[free1, free2, free3]).query(pts2)[0]
billow = .09 * np.minimum(dl, .1) * np.clip(de / .03, 0, 1)
mid = to3d(pts2, billow)
# root band: within 30 mm of the root edge the membrane bends down onto the body, 3 mm under its surface
dr, _ = seg_dist(pts2, S, R); band = np.clip(1 - dr / .03, 0, 1) ** 2
bx = body_x(mid[:, 1], mid[:, 2]) - .003
target = mid.copy(); target[:, 0] = np.minimum(mid[:, 0], bx)
mid = mid * (1 - band[:, None]) + target * band[:, None]

def mesh_normals(v, t):
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]); vn = np.zeros_like(v)
    for k in range(3): np.add.at(vn, t[:, k], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
nrm = mesh_normals(mid, tri)
top = mid + nrm * THICK; bot = mid - nrm * THICK
nm = len(pts2)
verts = [top, bot]; tris = [tri, tri[:, [0, 2, 1]] + nm]
kind = [np.zeros(nm, int), np.ones(nm, int)]; piece = [np.zeros(nm, int), np.zeros(nm, int)]
param = [pts2, pts2]
names, wm = membrane_weights(pts2); weights = [wm, wm]
# rim around the whole outline (outline vertices are 0..nb-1 in both layers)
i = np.arange(nb); j = (i + 1) % nb
rim = np.r_[np.c_[i, j, j + nm], np.c_[i, j + nm, i + nm]]
# outline is CCW, so its outward side is to the right of i->j: (i, j, j') faces outward when its normal points out
o = len(pts2)
rim_check = np.cross(np.r_[top][j] - np.r_[top][i], np.r_[bot][i] - np.r_[top][i])
out_dir = np.c_[np.r_[outline][j][:, 1] - np.r_[outline][i][:, 1], -(np.r_[outline][j][:, 0] - np.r_[outline][i][:, 0])]
out3 = out_dir[:, :1] * U + out_dir[:, 1:] * V
if np.mean(np.sum(rim_check * out3, 1)) < 0: rim = rim[:, [0, 2, 1]]
tris.append(rim)
offset = 2 * nm

# ---------------------------------------------------------------- tubes and claws
def frames(curve3):
    t = np.gradient(curve3, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    b = np.cross(t, N); b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9); n = np.cross(b, t); return t, n, b

def catmull(points, n_per):
    pts = np.array(points); out = []
    ext = np.r_[[2 * pts[0] - pts[1]], pts, [2 * pts[-1] - pts[-2]]]
    for k in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[k - 1:k + 3]
        for t in np.linspace(0, 1, n_per, endpoint=False):
            out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1]); return np.array(out)

tube_meta = []
def tube(name, ctrl2, radii, bones_along, cap_start=True, cap_end=False, start3=None, SIDES=6, ring=.02):
    """ctrl2: control points in the wing frame; radii: per control point; bones_along: (s_fraction, bone) list."""
    global offset
    c3 = to3d(np.array(ctrl2))
    if start3 is not None: c3[0] = start3
    curve = catmull(c3, 6)
    seg = np.linalg.norm(np.diff(curve, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    n = max(4, int(np.ceil(s[-1] / ring)) + 1); ts = np.linspace(0, s[-1], n)
    cur = np.c_[[np.interp(ts, s, curve[:, k]) for k in range(3)]].T
    sc = np.linspace(0, 1, len(radii)); r = np.interp(ts / s[-1], sc, radii)
    t, nn, bb = frames(cur)
    ang = np.linspace(0, 2 * np.pi, SIDES, endpoint=False)
    ring = cur[:, None, :] + r[:, None, None] * (np.cos(ang)[None, :, None] * nn[:, None, :] + np.sin(ang)[None, :, None] * bb[:, None, :])
    v = ring.reshape(-1, 3); tt = []
    for a in range(n - 1):
        for k in range(SIDES):
            k2 = (k + 1) % SIDES; p, q, rr, ss = a * SIDES + k, a * SIDES + k2, (a + 1) * SIDES + k2, (a + 1) * SIDES + k
            tt += [[p, q, rr], [p, rr, ss]]
    tt = np.array(tt)
    extra = []
    if cap_start:
        extra.append(cur[0] - t[0] * r[0] * .6); c = len(v) + len(extra) - 1
        tt = np.r_[tt, [[c, (k + 1) % SIDES, k] for k in range(SIDES)]]
    if cap_end:
        extra.append(cur[-1] + t[-1] * r[-1] * .6); c = len(v) + len(extra) - 1; b0 = (n - 1) * SIDES
        tt = np.r_[tt, [[c, b0 + k, b0 + (k + 1) % SIDES] for k in range(SIDES)]]
    v = np.r_[v, np.array(extra).reshape(-1, 3)]
    # orientation: first quad normal should point away from the curve
    f0 = np.cross(v[tt[0, 1]] - v[tt[0, 0]], v[tt[0, 2]] - v[tt[0, 0]])
    if f0 @ (v[tt[0, 0]] - cur[0]) < 0: tt = tt[:, [0, 2, 1]]
    # weights: along the curve, blend between consecutive bones over +-12 mm at their joints
    sf = ts / s[-1]; ws = []
    for x in sf:
        x_m = x * s[-1]; w = {}
        for k, (f, b) in enumerate(bones_along):
            nxt = bones_along[k + 1][0] if k + 1 < len(bones_along) else 1.01
            if f * s[-1] - .012 <= x_m < nxt * s[-1] + .012:
                lo = np.clip((x_m - (f * s[-1] - .012)) / .024, 0, 1) if k > 0 else 1.
                hi = np.clip(((nxt * s[-1] + .012) - x_m) / .024, 0, 1) if k + 1 < len(bones_along) else 1.
                w[b] = w.get(b, 0) + min(lo, hi)
        tot = sum(w.values()); ws.append({b: q / tot for b, q in w.items()})
    vw = [ws[i // SIDES] for i in range(n * SIDES)] + [ws[0] if cap_start else None, ws[-1] if cap_end else None]
    vw = [x for x in vw if x is not None]
    # unrolled UV params: (arc length, angle * radius)
    prm = np.c_[np.repeat(ts, SIDES), np.tile(ang, n) / (2 * np.pi)]
    prm = np.r_[prm, np.c_[[0.] * cap_start + [ts[-1]] * cap_end, [.5] * (cap_start + cap_end)]]
    tube_meta.append({'name': name, 'length': float(s[-1]), 'max_radius': float(r.max()), 'vertices': len(v), 'offset': offset,
                      'mean_circumference': float(2 * np.pi * r.mean())})
    verts.append(v); tris.append(tt + offset); kind.append(np.full(len(v), 3)); param.append(prm); piece.append(np.full(len(v), len(tube_meta)))
    W_ = np.zeros((len(v), len(names)))
    for i, w in enumerate(vw):
        for b, q in w.items(): W_[i, names.index(b)] = q
    weights.append(W_); offset += len(v)

arm_start = JOINT + (-.012) * U                              # starts inside the shoulder
tube('arm', [S, (S + E) / 2, E, (E + W) / 2, W], [.0165, .0145, .0115, .0105, .0098], [(0, 'Spine2'), (.10, 'Wing0'), (.45, 'Wing1')],
     cap_start=True, start3=arm_start, SIDES=8, ring=.016)
tube('F1', [W, (W + M1) / 2, M1, (M1 + T1) / 2, T1], [.0088, .0075, .0062, .0042, .0024], [(0, 'Wing2'), (.45, 'Wing3')], cap_start=True)
tube('F2', [W, (W * .6 + T2 * .4), T2], [.0068, .0048, .0022], [(0, 'WingF2')], cap_start=True)
tube('F3', [E, (E * .5 + T3 * .5), T3], [.0062, .0045, .0021], [(0, 'WingF3')], cap_start=True)

def claw(name, base3, direction, length, radius, curl, bone):
    """Curved cone: centreline bends by `curl` (rad) toward -n over its length; 6 sides, 5 rings, tip point."""
    global offset
    d = direction / np.linalg.norm(direction); side = np.cross(d, N); side /= np.linalg.norm(side); up = np.cross(side, d)
    rings = 5; pts = []; v = []
    for k in range(rings + 1):
        f = k / rings; a = curl * f
        c = base3 + length * (f * d * np.cos(a / 2) - f * up * np.sin(a / 2) * .5) if k else base3
        rr = radius * (1 - f) ** .9
        tdir = d * np.cos(a) - up * np.sin(a); s2 = np.cross(tdir, side); pts.append(c)
        if k < rings:
            for j in range(6):
                t = 2 * np.pi * j / 6; v.append(c + rr * (np.cos(t) * side + np.sin(t) * s2))
    v.append(pts[-1]); v = np.array(v); tt = []
    for k in range(rings - 1):
        for j in range(6):
            j2 = (j + 1) % 6; tt += [[k * 6 + j, k * 6 + j2, (k + 1) * 6 + j2], [k * 6 + j, (k + 1) * 6 + j2, (k + 1) * 6 + j]]
    tip = len(v) - 1; b = (rings - 1) * 6; tt += [[b + j, b + (j + 1) % 6, tip] for j in range(6)]
    tt = np.array(tt)
    f0 = np.cross(v[tt[0, 1]] - v[tt[0, 0]], v[tt[0, 2]] - v[tt[0, 0]])
    if f0 @ (v[tt[0, 0]] - base3) < 0: tt = tt[:, [0, 2, 1]]
    prm = np.c_[np.r_[np.repeat(np.arange(rings) / rings, 6), 1.], np.r_[np.tile(np.arange(6) / 6, rings), .5]]
    verts.append(v); tris.append(tt + offset); kind.append(np.full(len(v), 4)); param.append(prm); piece.append(np.full(len(v), len(tube_meta) + 1))
    W_ = np.zeros((len(v), len(names))); W_[:, names.index(bone)] = 1; weights.append(W_)
    tube_meta.append({'name': name, 'vertices': len(v), 'offset': offset}); offset += len(v)

w3 = to3d(np.array([W]))[0]; t1 = to3d(np.array([T1]))[0]; t2 = to3d(np.array([T2]))[0]; t3 = to3d(np.array([T3]))[0]
claw('thumb', w3 + .004 * N, -V * .8 + N * .55 + U * .1, .036, .0062, .9, 'Wing2')
claw('tip1', t1 - .002 * (t1 - to3d(np.array([M1]))[0]) / .2, t1 - to3d(np.array([M1]))[0], .022, .0026, .6, 'Wing3')
claw('tip2', t2, t2 - w3, .018, .0022, .6, 'WingF2')
claw('tip3', t3, t3 - to3d(np.array([E]))[0], .016, .0021, .6, 'WingF3')

V3 = np.concatenate(verts); T3_ = np.concatenate(tris); K = np.concatenate(kind); PR = np.concatenate(param); WW = np.concatenate(weights)
PC = np.concatenate(piece)

# ---------------------------------------------------------------- UV layout of the wing texture domain (0..1, v up)
layout = {}
mlo = pts2.min(0) - .004; mhi = pts2.max(0) + .004; km = min(.80 / (mhi[0] - mlo[0]), .685 / (mhi[1] - mlo[1]))
layout['membrane'] = {'origin_uv': [.01, .305], 'planform_min': mlo.tolist(), 'scale': km}
UV = np.zeros((len(V3), 2))
m = PC == 0; UV[m] = [.01, .305] + (PR[m] - mlo) * km
tubes = [t for t in tube_meta if 'length' in t]
kt = min(.275 / sum(t['mean_circumference'] + .012 for t in tubes), .975 / max(t['length'] for t in tubes))
y0 = .008
for i, t in enumerate(tubes):
    h = t['mean_circumference'] * kt; layout[t['name']] = {'origin_uv': [.012, y0], 'scale': kt, 'height_uv': h, 'length': t['length']}
    m = PC == i + 1; UV[m, 0] = .012 + PR[m, 0] * kt; UV[m, 1] = y0 + PR[m, 1] * h
    y0 += h + .012 * kt
claw_box = [.83, .315, .98, .455]; layout['claws'] = {'box': claw_box}
m = PC > len(tubes); UV[m, 0] = claw_box[0] + PR[m, 0] * (claw_box[2] - claw_box[0]); UV[m, 1] = claw_box[1] + PR[m, 1] * (claw_box[3] - claw_box[1])
layout['tube_count'] = len(tubes); layout['pieces'] = ['membrane'] + [t['name'] for t in tube_meta]
# bone rest positions (3D) for the rig
bone_pts = {n: [to3d(np.array([a]))[0].tolist(), to3d(np.array([b]))[0].tolist()] for n, (a, b) in BONES.items()}
bone_pts['Wing0'][0] = JOINT.tolist()
np.savez(OUT / 'wing_left.npz', co=V3, tris=T3_, kind=K, param=PR, weights=WW, names=np.array(names), piece=PC, uv=UV, layout=json.dumps(layout),
         outline=outline, pts2=pts2, nm=nm, bone_pts=json.dumps(bone_pts), tubes=json.dumps(tube_meta),
         frame=np.array([JOINT, U, V, N]))
print('WING', {'vertices': len(V3), 'triangles': len(T3_), 'membrane_points': nm, 'membrane_triangles_per_layer': len(tri),
               'tubes': [(m['name'], m['vertices']) for m in tube_meta]})
