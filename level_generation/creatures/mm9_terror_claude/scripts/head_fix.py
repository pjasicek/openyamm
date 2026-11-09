"""Head and UV repairs on the UV'd master (user review 2026-10-30): uv_v1.blend -> uv_v2.blend + work/head_fix.json.

Args: <uv blend> <out blend> <report json>

1. UV overlap. Smart UV Project flattened some long islands onto one plane, so faces of a long tentacle's tip and
   of the crotch/thigh share texels (green tentacle skin painted inside the blue belly). Overlapping face pairs are
   found by rasterising the old UVs at 2K; per pair, the face whose 3D neighbourhood colour differs most from the
   shared texels is the loser. Losers move, as islands, into the band freed by step 2; head_fix_tex.py repaints
   them from the clean surface around them in 3D.
2. Atlas band. Every other UV keeps its island and is squeezed to v * VSCALE (axis-aligned, so tangent directions and
   the normal map stay valid); the band v > VSCALE holds the mouth cavity, the relocated faces and the throat swatch.
3. Mouth cavity. The Meshy cavity (few faces, palate weighted to the lower jaw, so a wide MM9 jaw opening smeared
   it 8x) is replaced by a bag: rings from the inner lip loop back to the throat, following the old cavity surface
   (rays from the mouth axis), closed by a strip cap. Weights: upper half on the upper jaw (Bone37), lower half on
   the lower jaw (Bone35), a smooth fan between them by angle around the mouth axis, the roof blending to the head
   toward the throat, the first rings blending into the lip weights. UVs: one rectangular island (u around the
   mouth, seam at the bottom middle under the tongue; v along the depth), laid out from the bag's shape at a
   reference MM9 pose whose jaw gap is REF_RATIO times smaller than the widest MM9 opening, so the texture stays
   within about REF_RATIO x at the widest opening and is compressed when the mouth closes.
4. Teeth and tongue: rigid with the weights of the gum at their root (seated in the gum in every frame).
5. Eyes: each eyeball and its socket (body vertices within SOCKET_IN eyeball radii, fading out by SOCKET_OUT) take
   one anchor weight set, the socket's mean without tentacle-chain bones; the eyeball can no longer slide out.
Face attributes written: 'mouth_bag' (1 bag, 2 throat cap), 'relocated' (island id + 1).
"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(HERE, 'meshy', 'terror_retexture_v1', 'texture_urls_0_base_color.png')
TEX = 2048
VSCALE = 0.9
MARGIN = 8.0 / TEX
UPPER, LOWER, HEADB = 'Bone37', 'Bone35', 'Bip01 Head'
CHAIN_BONES = {'Bone26', 'Bone27', 'Bone28', 'Bone29', 'Bone30', 'Bone31', 'Bone32', 'Bone33', 'Bone01', 'Bone02',
               'Bone03', 'Bone04', 'Bone21', 'Bone22', 'Bone23', 'Bone24', 'Bone14', 'Bone15', 'Bone16', 'Bone05',
               'Bone06', 'Bone07', 'Bone13', 'Bone18', 'Bone19', 'Bone09', 'Bone10', 'Bone11'}
COLS, RINGS = 40, 14           # bag columns around the mouth, rings from the lip loop to the throat
FAN_BAND = 0.85                # sin(angle) band of the upper/lower fan
ROOF_TO_HEAD = 0.6             # roof weight given to the head at the throat
LIP_BLEND = 0.3                # depth fraction over which the bag leaves the lip loop's own weights
REF_RATIO = 1.5                # widest MM9 jaw gap / jaw gap of the UV reference pose
DENSITY = 300.0                # cavity texels per metre at 2K (head islands ~330 after the squeeze)
SOCKET_IN, SOCKET_OUT = 1.45, 2.2
LIP_ZONE = 0.15               # metres around the lip loop re-weighted by the jaw fan
JAW_ZONE = 0.3                # metres around the lip loop whose jaw-bone share is re-split by the fan
LOOP_SMOOTH = 3                # damped Laplacian steps along the lip loop
REF_ACTIONS = ('Hattack1', 'Hattack2', 'wince1', 'fidget1', 'die1', 'stand', 'walk', 'run')

bpy.ops.wm.open_mainfile(filepath=IN)
rig = bpy.data.objects['MM9_Rig']
ob = bpy.data.objects['Body']
me = ob.data
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
assert ob.matrix_world.is_identity and rig.matrix_world.is_identity
names = [g.name for g in ob.vertex_groups]
for b in (UPPER, LOWER, HEADB):
    if b not in names:
        ob.vertex_groups.new(name=b)
names = [g.name for g in ob.vertex_groups]
gi = {nm: i for i, nm in enumerate(names)}
n0 = len(me.vertices)
V = np.array([v.co[:] for v in me.vertices])
F = np.array([p.vertices[:] for p in me.polygons])
assert F.shape[1] == 3
uvl = me.uv_layers['UVMap'].data
UV = np.array([[uvl[l].uv[:] for l in p.loop_indices] for p in me.polygons])
piece = np.array([d.value for d in me.attributes['piece'].data])
W = np.zeros((n0, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
report = {'vscale': VSCALE, 'tex': TEX}

# ---------------------------------------------------------------- shells
par = np.arange(n0)


def find(a):
    while par[a] != a:
        par[a] = par[par[a]]
        a = par[a]
    return a


for t in F:
    for a, b in ((t[0], t[1]), (t[1], t[2])):
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
shell = np.array([find(i) for i in range(n0)])
sid, scnt = np.unique(shell, return_counts=True)
MAIN = sid[scnt.argmax()]
main_v = shell == MAIN
eyes, teeth, tongue = [], [], None
for s in sid:
    if s == MAIN:
        continue
    v = np.nonzero(shell == s)[0]
    ext = np.ptp(V[v], 0)
    if len(v) >= 60 and ext.max() / max(ext.min(), 1e-6) < 1.3:
        eyes.append(v)
    elif ext.max() > 0.4:
        tongue = v
    else:
        teeth.append(v)
kd_main = KDTree(int(main_v.sum()))
main_ids = np.nonzero(main_v)[0]
for j, i in enumerate(main_ids):
    kd_main.insert(V[i], j)
kd_main.balance()


def root_of(v):
    d = np.array([kd_main.find(V[i])[2] for i in v])
    return V[v[np.argsort(d)[:max(3, len(v) // 5)]]].mean(0)


roots = np.array([root_of(v) for v in teeth])
tips = np.array([V[v[np.argmax(np.linalg.norm(V[v] - r, axis=1))]] for v, r in zip(teeth, roots)])
report['pieces'] = {'eyes': len(eyes), 'teeth': len(teeth), 'tongue': int(len(tongue)) if tongue is not None else 0}

# ---------------------------------------------------------------- 1. UV overlap (old layout)
img = bpy.data.images.load(BASE)
S = img.size[0]
px = np.empty(S * S * 4, np.float32)
img.pixels.foreach_get(px)
px = px.reshape(S, S, 4)[..., :3]          # row 0 = v 0


def raster(p, eps):
    """Texels (rows from v=0, cols) strictly inside a UV triangle p (3x2, pixel units)."""
    x0, x1 = int(np.floor(p[:, 0].min())), int(np.ceil(p[:, 0].max()))
    y0, y1 = int(np.floor(p[:, 1].min())), int(np.ceil(p[:, 1].max()))
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = p
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        return np.zeros(0, int), np.zeros(0, int)
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    ins = (l1 > eps) & (l2 > eps) & (1 - l1 - l2 > eps)
    iy, ix = np.nonzero(ins)
    return np.clip(iy + y0, 0, S - 1), np.clip(ix + x0, 0, S - 1)


cover = np.zeros((S, S), np.int16)
owner = -np.ones((S, S), np.int32)
tpx = {}
pairs = {}
for t in range(len(F)):
    iy, ix = raster(UV[t] * S, 1e-2)
    tpx[t] = (iy, ix)
    prev = owner[iy, ix]
    for q in np.unique(prev[prev >= 0]):
        k = (int(q), t)
        pairs[k] = pairs.get(k, 0) + int((prev == q).sum())
    owner[iy, ix] = t
    cover[iy, ix] += 1
pairs = {k: c for k, c in pairs.items() if c >= 4}
in_pair = set(a for k in pairs for a in k)
cent = V[F].mean(1)
own = np.full((len(F), 3), np.nan)
for t, (iy, ix) in tpx.items():
    ok = cover[iy, ix] == 1
    if ok.sum() >= 4:
        own[t] = px[iy[ok], ix[ok]].mean(0)
kd_c = KDTree(len(F))
for t in range(len(F)):
    kd_c.insert(cent[t], t)
kd_c.balance()


def neighbourhood(t):
    for r in (0.06, 0.12, 0.25):
        cs = [own[u] for _, u, _ in kd_c.find_range(cent[t], r) if u not in in_pair and not np.isnan(own[u, 0])]
        if len(cs) >= 3:
            return np.mean(cs, 0)
    return own[t]


losers = set()
for (a, b), c in pairs.items():
    ia, xa = tpx[a]
    sa = set(zip(ia.tolist(), xa.tolist()))
    ib, xb = tpx[b]
    shared = [p for p in zip(ib.tolist(), xb.tolist()) if p in sa]
    if not shared:
        continue
    sc = px[tuple(np.array(shared).T)].mean(0)
    da, db = (np.linalg.norm(neighbourhood(x) - sc) for x in (a, b))
    losers.add(a if da >= db else b)
report['overlap'] = {'texels': int((cover > 1).sum()), 'pairs': len(pairs), 'relocated_faces': len(losers)}

bpy.data.images.remove(img)

# loser islands: faces sharing an edge with identical UVs
edge_key = {}
for t in losers:
    for k in range(3):
        a, b = F[t][k], F[t][(k + 1) % 3]
        ua, ub = tuple(np.round(UV[t][k], 6)), tuple(np.round(UV[t][(k + 1) % 3], 6))
        key = (a, ua, b, ub) if a < b else (b, ub, a, ua)
        edge_key.setdefault(key, []).append(t)
lp = {t: t for t in losers}


def lf(a):
    while lp[a] != a:
        lp[a] = lp[lp[a]]
        a = lp[a]
    return a


for ts in edge_key.values():
    for u in ts[1:]:
        lp[lf(u)] = lf(ts[0])
islands = {}
for t in losers:
    islands.setdefault(lf(t), []).append(t)
islands = list(islands.values())

# ---------------------------------------------------------------- 3. mouth cavity: segmentation
o0 = roots.mean(0)
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
oldf_l = bm.faces.layers.int.new('old_face')
bag_l = bm.faces.layers.int.get('mouth_bag') or bm.faces.layers.int.new('mouth_bag')
rel_l = bm.faces.layers.int.get('relocated') or bm.faces.layers.int.new('relocated')
deform = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
vref = list(bm.verts)          # (references stay valid: every layer exists before they are taken)
fref = list(bm.faces)
for f in bm.faces:
    f[oldf_l] = f.index + 1
main_faces = [f.index for f in bm.faces if main_v[f.verts[0].index]]
bvh_main = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(F[t]) for t in main_faces])
hit = bvh_main.ray_cast(Vector(o0), Vector((0, 1, 0)), 3.0)
th = np.array(hit[0])
A = (th - o0) / np.linalg.norm(th - o0)
ex = np.cross(A, [0, 0, 1.0])
ex = ex / np.linalg.norm(ex)        # +X (the creature faces -Y)
ez = np.cross(ex, A)
ez = ez if ez[2] > 0 else -ez
nrm = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
s_f = (cent - o0) @ A
rad = (cent - o0) - np.outer(s_f, A)
r_f = np.linalg.norm(rad, axis=1)
rr = (roots - o0)
rx, rz = np.abs(rr @ ex).max() * 1.15 + 0.03, np.abs(rr @ ez).max() * 1.1 + 0.03
rho = np.hypot((cent - o0) @ ex / rx, (cent - o0) @ ez / rz)
# the cavity: body faces inside the elliptic cylinder through the gum line (teeth roots, widened), behind the lip front
# lip fronts (facing out of the mouth) stay: the cut follows the lip rim where the surface turns into the mouth
interior = main_v[F[:, 0]] & (s_f > -0.12) & (rho < 1.0) & ~((nrm @ -A > 0.55) & (s_f < 0.12))
fadj = [[] for _ in F]
ef = {}
for t in main_faces:
    for k in range(3):
        a, b = F[t][k], F[t][(k + 1) % 3]
        ef.setdefault((min(a, b), max(a, b)), []).append(t)
for ts in ef.values():
    for a in ts:
        fadj[a] += [b for b in ts if b != a]


def grow(mask, seed):
    reg = np.zeros(len(F), bool)
    reg[seed] = True
    st = [seed]
    while st:
        t = st.pop()
        for u in fadj[t]:
            if mask[u] and not reg[u]:
                reg[u] = True
                st.append(u)
    return reg


seed = int(np.argmin(np.where(interior, np.linalg.norm(cent - th, axis=1), 9)))
region = grow(interior, seed)
mainmask = np.zeros(len(F), bool)
mainmask[main_faces] = True
comp = -np.ones(len(F), int)
k = 0
for t in np.nonzero(mainmask & ~region)[0]:
    if comp[t] >= 0:
        continue
    comp[t] = k
    st = [t]
    while st:
        x = st.pop()
        for u in fadj[x]:
            if not region[u] and comp[u] < 0:
                comp[u] = k
                st.append(u)
    k += 1
big = np.bincount(comp[comp >= 0]).argmax()
region |= mainmask & (comp >= 0) & (comp != big)
# lip loop: edges between a cavity face and a kept face (open mesh holes inside the cavity go with it)
bedges = [e for e, ts in ef.items() if len(ts) == 2 and sum(region[t] for t in ts) == 1]
report_holes = sum(1 for e, ts in ef.items() if len(ts) == 1 and region[ts[0]])
nbr = {}
for a, b in bedges:
    nbr.setdefault(a, []).append(b)
    nbr.setdefault(b, []).append(a)
np.save(os.path.join(HERE, 'work', 'head_fix_region.npy'), region)
assert all(len(x) == 2 for x in nbr.values()), 'lip loop is not simple'
loops, seen = [], set()
for a0 in nbr:
    if a0 in seen:
        continue
    lp_ = [a0]
    seen.add(a0)
    prev = None
    while True:
        cur = lp_[-1]
        nx = [x for x in nbr[cur] if x != prev][0]
        if nx == lp_[0]:
            break
        prev = cur
        lp_.append(nx)
        seen.add(nx)
    loops.append(lp_)
assert len(loops) == 1, 'more than one lip loop'
loop = np.array(loops[0])
# smooth the lip loop along itself (it zigzags through the lip triangles): a few damped Laplacian steps on the
# loop vertices only; the lip faces around them keep their UVs
for _ in range(LOOP_SMOOTH):
    q = V[loop]
    V[loop] = q + 0.5 * (0.5 * (np.roll(q, 1, 0) + np.roll(q, -1, 0)) - q)
for i in loop:
    vref[i].co = Vector(V[i])
np.save(os.path.join(HERE, 'work', 'head_fix_loop.npy'), V[loop])


def ang(p):
    q = p - o0
    return np.arctan2(q @ ez, q @ ex)


phi_l = ang(V[loop])
if np.sum(np.diff(np.unwrap(phi_l))) < 0:
    loop = loop[::-1]
    phi_l = phi_l[::-1]
# start the loop at the bottom middle (the seam)
start = int(np.argmin(np.abs(((phi_l + math.pi / 2) + math.pi) % (2 * math.pi) - math.pi)))
loop = np.roll(loop, -start)
phi_l = np.roll(phi_l, -start)
report['cavity'] = {'faces_replaced': int(region.sum()), 'lip_loop_verts': int(len(loop)),
                    'axis_start': o0.round(4).tolist(), 'throat': th.round(4).tolist()}

# ---------------------------------------------------------------- 3b. bag geometry
reg_faces = np.nonzero(region)[0]
report['cavity_old_uv'] = UV[reg_faces].round(6).tolist()   # the Meshy mouth paint, sampled by compose
np.savez(os.path.join(HERE, 'work', 'head_fix_cavity_v1.npz'),            # for seat_check.py on the v1 build
         centroids_gltf=np.stack([cent[reg_faces, 0], cent[reg_faces, 2], -cent[reg_faces, 1]], 1))
bvh_cav = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(F[t]) for t in reg_faces])
P_loop = V[loop]
s_loop = (P_loop - o0) @ A
u_loop = np.unwrap(phi_l) + math.pi / 2               # 0 .. 2 pi from the seam
u_loop = u_loop - u_loop[0]
# loop as a closed curve by angle: point at any angle
lp_ang = np.concatenate([u_loop, [2 * math.pi]])
lp_pts = np.concatenate([P_loop, P_loop[:1]])


def loop_at(a):
    a = a % (2 * math.pi)
    i = int(np.searchsorted(lp_ang, a, side='right')) - 1
    i = min(max(i, 0), len(lp_ang) - 2)
    f = (a - lp_ang[i]) / max(lp_ang[i + 1] - lp_ang[i], 1e-9)
    return lp_pts[i] * (1 - f) + lp_pts[i + 1] * f


s_end = float((th - o0) @ A) - 0.025


def resample(pts, m):
    """m points at equal arc length along a polyline."""
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    out = []
    for x in np.linspace(0, cum[-1], m):
        i = min(int(np.searchsorted(cum, x, side='right')) - 1, len(seg) - 1)
        out.append(pts[i] + (pts[i + 1] - pts[i]) * (x - cum[i]) / max(seg[i], 1e-9))
    return np.array(out)


FINE = 80
cols = []
for j in range(COLS):
    a = 2 * math.pi * j / COLS
    phi = a - math.pi / 2
    d = math.cos(phi) * ex + math.sin(phi) * ez
    p0 = loop_at(a)
    s0 = float((p0 - o0) @ A)
    pts = [p0]
    last_r = float(np.linalg.norm((p0 - o0) - ((p0 - o0) @ A) * A))
    for q in range(1, FINE + 1):
        s = s0 + (s_end - s0) * q / FINE
        ax = o0 + s * A
        h = bvh_cav.ray_cast(Vector(ax), Vector(d), 1.0)
        r = h[3] if h[0] is not None else last_r
        r = min(r, last_r * 1.15 + 0.01)
        last_r = r
        pts.append(ax + d * r)
    cols.append(resample(np.array(pts), RINGS + 1))
cols = np.array(cols)          # (COLS, RINGS+1, 3); ring 0 lies on the lip loop curve
# shrink the last ring to a slit toward the axis so the cap is small
endc = o0 + s_end * A
cols[:, RINGS] = endc + (cols[:, RINGS] - endc) * np.array([0.35, 0.35, 0.35])

# ---------------------------------------------------------------- 3c. bag faces
bm.verts.ensure_lookup_table()
piece_l = bm.verts.layers.int.get('piece')
chain_l = bm.verts.layers.int.get('chain')
uv_l = bm.loops.layers.uv['UVMap']
ring = [[vref[i] for i in loop]]
for k in range(1, RINGS + 1):
    rv = []
    for j in range(COLS):
        v = bm.verts.new(Vector(cols[j, k]))
        if piece_l:
            v[piece_l] = 0
        if chain_l:
            v[chain_l] = -1
        rv.append(v)
    ring.append(rv)
bm.verts.ensure_lookup_table()
bm.verts.index_update()
new_faces = []        # (face, kind)


def tri(a, b, c, kind):
    f = bm.faces.new((a, b, c))
    new_faces.append((f, kind))
    return f


# zipper ring 0 (loop, by angle u_loop) <-> ring 1 (uniform columns)
ua = list(u_loop) + [2 * math.pi]
ub = [2 * math.pi * j / COLS for j in range(COLS)] + [2 * math.pi]
i = j = 0
nl = len(loop)
while i < nl or j < COLS:
    a0, a1 = ring[0][i % nl], ring[0][(i + 1) % nl]
    b0, b1 = ring[1][j % COLS], ring[1][(j + 1) % COLS]
    if j >= COLS or (i < nl and ua[i + 1] <= ub[j + 1]):
        tri(a0, a1, b0, 1)
        i += 1
    else:
        tri(a0, b1, b0, 1)
        j += 1
for k in range(1, RINGS):
    for j in range(COLS):
        a, b = ring[k][j], ring[k][(j + 1) % COLS]
        c, d = ring[k + 1][(j + 1) % COLS], ring[k + 1][j]
        if (a.co - c.co).length <= (b.co - d.co).length:
            tri(a, b, c, 1)
            tri(a, c, d, 1)
        else:
            tri(a, b, d, 1)
            tri(b, c, d, 1)
# cap: strip between the lower chain (columns 0..COLS/2, bottom middle -> top middle along +angle side)
# and the other side (columns COLS..COLS/2 going the other way)
half = COLS // 2
left = [ring[RINGS][j] for j in range(0, half + 1)]
right = [ring[RINGS][(COLS - j) % COLS] for j in range(0, half + 1)]
for j in range(half):
    a, b = left[j], left[j + 1]
    c, d = right[j + 1], right[j]
    if j == 0:
        tri(a, b, c, 2)      # left[0] == right[0]
    elif j == half - 1:
        tri(a, b, d, 2)      # left[half] == right[half]
    else:
        tri(a, b, c, 2)
        tri(a, c, d, 2)
# orientation: a zipper face must traverse its lip edge opposite to the kept outer face
reg_set = set(int(t) for t in reg_faces)
flip = None
for f, kind in new_faces:
    vs = [v.index for v in f.verts]
    for k in range(3):
        a, b = vs[k], vs[(k + 1) % 3]
        e = (min(a, b), max(a, b))
        if a < n0 and b < n0 and e in ef:
            outer = [t for t in ef[e] if t not in reg_set]
            if outer:
                ov = list(F[outer[0]])
                ka = ov.index(a)
                same = ov[(ka + 1) % 3] == b
                flip = same
                break
    if flip is not None:
        break
assert flip is not None
if flip:
    for f, _ in new_faces:
        f.normal_flip()
for f, kind in new_faces:
    f[bag_l] = kind
    f.smooth = True
bm.normal_update()
inward = np.mean([(Vector(o0 + ((Vector(f.calc_center_median()) - Vector(o0)).dot(Vector(A))) * A)
                   - f.calc_center_median()).normalized().dot(f.normal) for f, k in new_faces if k == 1])
report['cavity']['bag_normals_inward'] = round(float(inward), 3)

# ---------------------------------------------------------------- 3d. bag weights
def row(d):
    w = np.zeros(len(names))
    for k, x in d.items():
        w[gi[k]] += x
    return w


Wu, Wl, Wh = row({UPPER: 1}), row({LOWER: 1}), row({HEADB: 1})


def smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# lip zone: the Meshy lip rim inherited lower-jaw weights all around (the palate side too), so the upper lip was
# torn between the jaws. Body vertices within LIP_ZONE of the lip loop (not tentacle roots) blend toward the same fan
# (upper jaw above the mouth axis, lower below, halfway at the corners); the loop itself takes the fan fully.
# Tentacle-root vertices keep their chain weights unless they are next to the loop.
def fan_target(p):
    q = p - o0
    s_up = smooth(-FAN_BAND, FAN_BAND, math.sin(math.atan2(q @ ez, q @ ex)))
    return s_up * Wu + (1 - s_up) * Wl


kd_loop = KDTree(len(loop))
for j, i in enumerate(loop):
    kd_loop.insert(V[i], j)
kd_loop.balance()
chain_idx = [gi[b] for b in CHAIN_BONES if b in gi]
reg_verts = set(F[region].ravel().tolist()) - set(F[mainmask & ~region].ravel().tolist())   # deleted with the cavity
# wider jaw zone: the jaw share of each vertex (upper + lower jaw bones) is re-split by the same fan, so no vertex
# above the mouth keeps lower-jaw weight (or below it upper-jaw weight); head and tentacle weights stay
U_BONES = [gi[b] for b in ('Bone37', 'Bone38') if b in gi]
L_BONES = [gi[b] for b in ('Bone35', 'Bone36', 'Bone39', 'Bone40', 'Bone41') if b in gi]
jaw_zone = 0
for i in np.nonzero(main_v)[0]:
    d = kd_loop.find(V[i])[2]
    if d >= JAW_ZONE or i in reg_verts:
        continue
    jw = W[i, U_BONES].sum() + W[i, L_BONES].sum()
    if jw < 1e-6:
        continue
    q = V[i] - o0
    s_up = smooth(-FAN_BAND, FAN_BAND, math.sin(math.atan2(q @ ez, q @ ex)))
    new = W[i].copy()
    new[U_BONES] = 0
    new[L_BONES] = 0
    new[gi[UPPER]] += jw * s_up
    new[gi[LOWER]] += jw * (1 - s_up)
    m = 1 - smooth(0.6 * JAW_ZONE, JAW_ZONE, d)
    W[i] = (1 - m) * W[i] + m * new
    jaw_zone += 1
report['cavity']['jaw_zone_verts'] = jaw_zone
lip_zone = []
for i in np.nonzero(main_v)[0]:
    if i in reg_verts:
        continue
    d = kd_loop.find(V[i])[2]
    if d < LIP_ZONE and (W[i, chain_idx].sum() < 0.2 or d < 0.35 * LIP_ZONE):
        m = 1 - smooth(0.35 * LIP_ZONE, LIP_ZONE, d)
        W[i] = (1 - m) * W[i] + m * fan_target(V[i])
        lip_zone.append(int(i))
report['cavity']['lip_zone_verts'] = len(lip_zone)
Wl0 = W[loop]
Wl0_ang = np.concatenate([Wl0, Wl0[:1]])


def lipw_at(a):
    a = a % (2 * math.pi)
    i = int(np.searchsorted(lp_ang, a, side='right')) - 1
    i = min(max(i, 0), len(lp_ang) - 2)
    f = (a - lp_ang[i]) / max(lp_ang[i + 1] - lp_ang[i], 1e-9)
    return Wl0_ang[i] * (1 - f) + Wl0_ang[i + 1] * f


def fan(a, fr):
    phi = a - math.pi / 2
    s_up = smooth(-FAN_BAND, FAN_BAND, math.sin(phi))
    g = ROOF_TO_HEAD * smooth(0.35, 1.0, fr) * s_up
    w = (1 - g) * (s_up * Wu + (1 - s_up) * Wl) + g * Wh
    m = smooth(0.0, LIP_BLEND, fr)
    return (1 - m) * lipw_at(a) + m * w


bag_w = {}
for k in range(1, RINGS + 1):
    for j in range(COLS):
        bag_w[ring[k][j]] = fan(2 * math.pi * j / COLS, k / RINGS)

# ---------------------------------------------------------------- delete the old cavity
old_faces = [fref[int(t)] for t in reg_faces]
bmesh.ops.delete(bm, geom=old_faces, context='FACES_ONLY')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
for i in np.nonzero(main_v)[0]:
    if i not in reg_verts and kd_loop.find(V[i])[2] < JAW_ZONE:
        bag_w[vref[i]] = W[i]
for v, w in bag_w.items():
    dv = v[deform]
    dv.clear()
    order = np.argsort(-w)[:4]
    tot = w[order].sum()
    for o in order:
        if w[o] / tot > 0.01:
            dv[int(o)] = float(w[o] / tot)

# ---------------------------------------------------------------- 4/5. teeth, tongue, eyes (weights by bmesh vertex)
def weights_of(v):
    w = np.zeros(len(names))
    for g, x in v[deform].items():
        w[g] = x
    return w


def set_rigid(vs, w):
    order = np.argsort(-w)[:4]
    w2 = np.where(np.isin(np.arange(len(w)), order), w, 0)
    w2[w2 < 0.15 * w2.max()] = 0
    w2 /= w2.sum()
    for v in vs:
        dv = v[deform]
        dv.clear()
        for o in np.nonzero(w2)[0]:
            dv[int(o)] = float(w2[o])
    return w2


vmap = vref
body_bm = [v for v in bm.verts if v[piece_l] == 0] if piece_l else list(bm.verts)
kd_b = KDTree(len(body_bm))
for k, v in enumerate(body_bm):
    kd_b.insert(v.co, k)
kd_b.balance()
teeth_rep = []
for v_ids, r in zip(teeth, roots):
    near = kd_b.find_n(Vector(r), 6)                    # the gum right around the root, inverse-distance weighted
    iw = np.array([1 / (d + 0.005) for _, _, d in near])
    w = (np.array([weights_of(body_bm[k]) for _, k, _ in near]) * iw[:, None]).sum(0) / iw.sum()
    w2 = set_rigid([vmap[i] for i in v_ids], w)
    teeth_rep.append({names[o]: round(float(w2[o]), 3) for o in np.nonzero(w2)[0]})
if tongue is not None:
    set_rigid([vmap[i] for i in tongue], Wl)
eye_rep = []
for v_ids in eyes:
    c = V[v_ids].mean(0)
    r = float(np.linalg.norm(V[v_ids] - c, axis=1).mean())
    sock = [(k, d) for _, k, d in kd_b.find_range(Vector(c), SOCKET_OUT * r)]
    inner = [k for k, d in sock if d < SOCKET_IN * r]
    w = np.mean([weights_of(body_bm[k]) for k in inner], 0)
    w[[gi[b] for b in CHAIN_BONES if b in gi]] = 0
    w[w < 0.25 * w.max()] = 0
    w /= w.sum()
    set_rigid([vmap[i] for i in v_ids], w)
    for k, d in sock:
        m = 1 - smooth(SOCKET_IN * r, SOCKET_OUT * r, d)
        v = body_bm[k]
        ww = (1 - m) * weights_of(v) + m * w
        order = np.argsort(-ww)[:4]
        tot = ww[order].sum()
        dv = v[deform]
        dv.clear()
        for o in order:
            if ww[o] / tot > 0.01:
                dv[int(o)] = float(ww[o] / tot)
    eye_rep.append({'centre': c.round(3).tolist(), 'radius': round(r, 3), 'socket_verts': len(sock),
                    'anchor': {names[o]: round(float(w[o]), 3) for o in np.nonzero(w)[0]}})
report['eyes'] = eye_rep
report['teeth'] = teeth_rep

# ---------------------------------------------------------------- 2. old UVs squeezed, losers relocated
band0, band1 = VSCALE + MARGIN, 1.0 - MARGIN
shelf_x, shelf_y, shelf_h = None, None, 0.0
placements = []


def place(w, h):
    """Shelf packing inside the band, right of the cavity island; returns the lower-left corner."""
    global shelf_x, shelf_y, shelf_h
    if shelf_x + w > 1.0 - MARGIN:
        shelf_x, shelf_y, shelf_h = place.x0, shelf_y + shelf_h + MARGIN, 0.0
    assert shelf_y + h <= band1, 'atlas band full'
    p = (shelf_x, shelf_y)
    shelf_x += w + MARGIN
    shelf_h = max(shelf_h, h)
    return p


# ---------------------------------------------------------------- 3e. cavity UVs at the reference pose
# gap at the gum line: mean root of the upper teeth (tips down) carried by the upper jaw, of the lower teeth by the
# lower jaw
up_pt = roots[tips[:, 2] < roots[:, 2]].mean(0)
lo_pt = roots[tips[:, 2] >= roots[:, 2]].mean(0)
sc = bpy.context.scene
bU, bL = rig.data.bones[UPPER], rig.data.bones[LOWER]


def gap():
    mu = rig.pose.bones[UPPER].matrix @ bU.matrix_local.inverted()
    ml = rig.pose.bones[LOWER].matrix @ bL.matrix_local.inverted()
    return ((mu @ Vector(up_pt)) - (ml @ Vector(lo_pt))).length


rig.animation_data_create()
best = (0, None, 0)
gaps = {}
for an in REF_ACTIONS:
    act = bpy.data.actions.get(an)
    if act is None:
        continue
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    f0, f1 = (int(x) for x in act.frame_range)
    seq = []
    for fr in range(f0, f1 + 1):
        sc.frame_set(fr)
        seq.append(gap())
    gaps[an] = seq
    k = int(np.argmax(seq))
    if seq[k] > best[0]:
        best = (seq[k], an, f0 + k)
g_max, act_max, fr_max = best
target = g_max / REF_RATIO
seq = gaps[act_max]
f0 = int(bpy.data.actions[act_max].frame_range[0])
# the reference: where the opening first crosses the target gap before the widest frame (bisection on subframes)
rig.animation_data.action = bpy.data.actions[act_max]
cross = next(i for i in range(fr_max - f0) if seq[i] <= target <= seq[i + 1]) if seq[0] <= target else 0
lo_f, hi_f = float(f0 + cross), float(f0 + cross + 1)
for _ in range(20):
    mid = 0.5 * (lo_f + hi_f)
    sc.frame_set(int(mid), subframe=mid - int(mid))
    lo_f, hi_f = (mid, hi_f) if gap() < target else (lo_f, mid)
ref_fr = 0.5 * (lo_f + hi_f)
sc.frame_set(int(ref_fr), subframe=ref_fr - int(ref_fr))
ref_gap = gap()
# write weights/geometry into the mesh to evaluate the bag at the reference pose
bm.verts.index_update()
bm.faces.index_update()
loop_idx = [v.index for v in ring[0]]
ring_idx = [[v.index for v in r] for r in ring]
bm.to_mesh(me)
me.update()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
em = ev.to_mesh()
REFP = np.array([v.co[:] for v in em.vertices])
ev.to_mesh_clear()
report['cavity']['reference'] = {'action': act_max, 'frame': round(ref_fr, 3), 'gap': round(ref_gap, 3),
                                  'widest_gap': round(g_max, 3), 'widest': [act_max, fr_max],
                                  'bind_gap': round(float(np.linalg.norm(up_pt - lo_pt)), 3)}
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
bm.free()
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
bag_l = bm.faces.layers.int['mouth_bag']
rel_l = bm.faces.layers.int['relocated']
uv_l = bm.loops.layers.uv['UVMap']
oldf_l = bm.faces.layers.int['old_face']
R = [REFP[r] for r in ring_idx]


def ring_u(P):
    seg = np.linalg.norm(np.diff(np.concatenate([P, P[:1]]), axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    return cum[:-1] / cum[-1], cum[-1]


# Rectangular island, measured at the reference pose. Every column is a vertical line: its u is the mean normalised
# arc-length position of that column over the rings; ring 0 (the lip loop) takes u by angle between the columns.
# v = ring fraction (rings sit at equal arc length along each column) times the longest column, so no column and no
# ring is stretched beyond its reference length (shorter columns and rings are compressed).
ref_loop = np.concatenate([R[0], R[0][:1]])


def ref_loop_at(a):
    a = a % (2 * math.pi)
    i = min(max(int(np.searchsorted(lp_ang, a, side='right')) - 1, 0), len(lp_ang) - 2)
    f = (a - lp_ang[i]) / max(lp_ang[i + 1] - lp_ang[i], 1e-9)
    return ref_loop[i] * (1 - f) + ref_loop[i + 1] * f


col_u = np.mean([ring_u(R[k])[0] for k in range(1, RINGS)], 0)
col_u = np.append(col_u, 1.0)
pers = [ring_u(R[k])[1] for k in range(RINGS + 1)]
col_len = []
for j in range(COLS):
    p = [ref_loop_at(2 * math.pi * j / COLS)] + [R[k][j] for k in range(1, RINGS + 1)]
    col_len.append(float(np.sum(np.linalg.norm(np.diff(np.array(p), axis=0), axis=1))))
L_max = max(col_len)
seg_max = [max(float(np.linalg.norm(R[k][j] - R[k - 1][j])) for j in range(COLS)) for k in range(2, RINGS + 1)]
depth = [0.0, L_max / RINGS]
for x in seg_max:
    depth.append(depth[-1] + max(x, 0.5 * L_max / RINGS))
us = [None] * (RINGS + 1)
for k in range(1, RINGS + 1):
    us[k] = col_u[:COLS]
a_cols = 2 * math.pi / COLS
U_m = max(pers[1:])
# per vertex (u, v) in metres; ring 0 is unfolded onto the strip in front of ring 1: offset from the ring-1 point at
# its angle along the ring direction (u) and the column direction (v), so the jagged lip loop keeps its true shape
uvm = {}
for k in range(1, RINGS + 1):
    for j, vi in enumerate(ring_idx[k]):
        uvm[vi] = (col_u[j] * U_m, depth[k])
for l, vi in enumerate(ring_idx[0]):
    a = u_loop[l] % (2 * math.pi)
    j0 = min(int(a / a_cols), COLS - 1)
    f = a / a_cols - j0
    j1 = (j0 + 1) % COLS
    Q = R[1][j0] * (1 - f) + R[1][j1] * f
    Q2 = R[2][j0] * (1 - f) + R[2][j1] * f
    tu = R[1][j1] - R[1][j0]
    tu /= np.linalg.norm(tu) + 1e-12
    tv = Q2 - Q
    tv -= tu * (tv @ tu)
    tv /= np.linalg.norm(tv) + 1e-12
    dlt = R[0][l] - Q
    uq = (col_u[j0] * (1 - f) + col_u[j0 + 1] * f) * U_m
    uvm[vi] = (uq + dlt @ tu, depth[1] + min(dlt @ tv, -0.25 * depth[1]))
face_uv = {}
for f in bm.faces:
    if f[bag_l] == 1:
        uu = [uvm[l.vert.index][0] for l in f.loops]
        if max(uu) - min(uu) > 0.5 * U_m:
            uu = [x + U_m if x < 0.5 * U_m else x for x in uu]
        face_uv[f] = [(x, uvm[l.vert.index][1]) for x, l in zip(uu, f.loops)]
# The lip strip (faces touching ring 0) is solved as a least-squares conformal map (LSCM) of its reference-pose
# shape with the ring-1 UVs held: the unfolding above is only the start, it folds where the loop turns sharply.
ring0 = set(ring_idx[0])
strip = [f for f in face_uv if any(l.vert.index in ring0 for l in f.loops)]
keys, kidx = [], {}
for f in strip:
    for l, (x, y) in zip(f.loops, face_uv[f]):
        if l.vert.index in ring0:
            key = (l.vert.index, x >= U_m)
            if key not in kidx:
                kidx[key] = len(keys)
                keys.append(key)


def local2d(f, flipy):
    p = [REFP[l.vert.index] for l in f.loops]
    e1 = p[1] - p[0]
    L1 = np.linalg.norm(e1)
    e1 /= L1
    nn = np.cross(p[1] - p[0], p[2] - p[0])
    e2 = np.cross(nn, e1)
    e2 /= np.linalg.norm(e2)
    z = [0j, complex(L1, 0), complex((p[2] - p[0]) @ e1, (p[2] - p[0]) @ e2)]
    return [c.conjugate() for c in z] if flipy else z


# orientation of the held layout against the surface (the bag rings), so LSCM fits the same handedness
ref_face = next(f for f in face_uv if f not in strip)
zr = local2d(ref_face, False)
uvr = [complex(*q) for q in face_uv[ref_face]]
flipy = ((uvr[1] - uvr[0]).conjugate() * (uvr[2] - uvr[0])).imag * \
        ((zr[1] - zr[0]).conjugate() * (zr[2] - zr[0])).imag < 0
rows_a, rows_b = [], []
for f in strip:
    z = local2d(f, flipy)
    area = abs(((z[1] - z[0]).conjugate() * (z[2] - z[0])).imag) / 2
    if area < 1e-10:
        continue
    Wc = [(z[2] - z[1]), (z[0] - z[2]), (z[1] - z[0])]
    Wc = [w / math.sqrt(area) for w in Wc]
    re, im = np.zeros(2 * len(keys)), np.zeros(2 * len(keys))
    bre = bim = 0.0
    for w, l, (x, y) in zip(Wc, f.loops, face_uv[f]):
        key = (l.vert.index, x >= U_m)
        # (wr + i wi)(u + i v): real wr u - wi v, imaginary wr v + wi u
        if key in kidx:
            k = kidx[key]
            re[2 * k], re[2 * k + 1] = w.real, -w.imag
            im[2 * k], im[2 * k + 1] = w.imag, w.real
        else:
            bre -= w.real * x - w.imag * y
            bim -= w.real * y + w.imag * x
    rows_a += [re, im]
    rows_b += [bre, bim]
sol = np.linalg.lstsq(np.array(rows_a), np.array(rows_b), rcond=None)[0].reshape(-1, 2)
for f in strip:
    face_uv[f] = [tuple(sol[kidx[(l.vert.index, x >= U_m)]]) if (l.vert.index, x >= U_m) in kidx else (x, y)
                  for l, (x, y) in zip(f.loops, face_uv[f])]
report['cavity']['lip_strip_lscm'] = {'faces': len(strip), 'unknowns': len(keys), 'mirrored': bool(flipy)}
allm = np.array([p for q in face_uv.values() for p in q])
u_lo, v_lo = allm.min(0)
u_hi, v_hi = allm.max(0)
d_uv = DENSITY / TEX
avail = band1 - band0
if (v_hi - v_lo) * d_uv > avail:
    d_uv *= avail / ((v_hi - v_lo) * d_uv)
w_uv, h_uv = (u_hi - u_lo) * d_uv, (v_hi - v_lo) * d_uv
bag_x0, bag_y0 = MARGIN, band0
cap_px = 24.0 / TEX
place.x0 = bag_x0 + w_uv + MARGIN
shelf_x, shelf_y, shelf_h = place.x0, band0, 0.0
cap_x0, cap_y0 = place(cap_px, cap_px)
for f in bm.faces:
    if f[bag_l] == 1:
        for l, (x, y) in zip(f.loops, face_uv[f]):
            l[uv_l].uv = (bag_x0 + (x - u_lo) * d_uv, bag_y0 + (y - v_lo) * d_uv)
    elif f[bag_l] == 2:
        for l in f.loops:
            p = np.array(l.vert.co) - (o0 + s_end * A)        # bind pose, around the throat centre
            l[uv_l].uv = (cap_x0 + cap_px * (0.5 + 0.5 * float(np.clip(p @ ex / 0.12, -1, 1))),
                          cap_y0 + cap_px * (0.5 + 0.5 * float(np.clip(p @ ez / 0.12, -1, 1))))
report['cavity']['u_metres'] = [round(float(u_lo), 3), round(U_m, 3), round(float(u_hi), 3)]
report['cavity']['v_metres'] = [round(float(v_lo), 3), round(depth[1], 3), round(depth[-1], 3)]
report['cavity']['seam_u'] = [round(float(-u_lo / (u_hi - u_lo)), 4), round(float((U_m - u_lo) / (u_hi - u_lo)), 4)]
report['cavity']['column_length_m'] = [round(min(col_len), 3), round(L_max, 3)]
report['cavity']['ring_perimeter_m'] = [round(x, 3) for x in pers]
report['cavity']['uv_rect'] = [bag_x0, bag_y0, bag_x0 + w_uv, bag_y0 + h_uv]
report['cavity']['uv_rect_gltf'] = [bag_x0, 1 - (bag_y0 + h_uv), bag_x0 + w_uv, 1 - bag_y0]
report['cavity']['cap_rect'] = [cap_x0, cap_y0, cap_x0 + cap_px, cap_y0 + cap_px]
report['cavity']['texels_per_metre'] = round(d_uv * TEX, 1)
report['cavity']['rings'] = RINGS
report['cavity']['columns'] = COLS
report['cavity']['ring_depth_m'] = [round(x, 4) for x in depth]
report['cavity']['axis'] = {'o': o0.tolist(), 'A': A.tolist(), 'ex': ex.tolist(), 'ez': ez.tolist(),
                            's_end': s_end}

# old faces: squeeze v, relocate the loser islands
reloc = []
isl_of = {t: k for k, isl in enumerate(islands) for t in isl}
isl_off = {}
dims = [(i, UV[islands[i]].reshape(-1, 2).min(0), UV[islands[i]].reshape(-1, 2).max(0)) for i in range(len(islands))]
avail_h = band1 - band0
# an island taller than the band is turned by 90 degrees (compose rotates its normal-map vectors with it)
rot = {i: bool(hi[1] - lo[1] > avail_h and hi[0] - lo[0] < hi[1] - lo[1]) for i, lo, hi in dims}
R90 = np.array([[0.0, -1.0], [1.0, 0.0]])


def isl_size(i, lo, hi):
    d = hi - lo
    return d[::-1] if rot[i] else d


dims.sort(key=lambda d: -isl_size(*d)[1])
start_state = (shelf_x, shelf_y, shelf_h)
isl_scale = 1.0
while True:
    shelf_x, shelf_y, shelf_h = start_state
    try:
        isl_off = {i: (lo, hi, np.array(place(*(isl_size(i, lo, hi) * isl_scale)))) for i, lo, hi in dims}
        break
    except AssertionError:
        isl_scale *= 0.95


def isl_map(i, uv):
    """old UV(s) of island i -> new UV(s)."""
    lo, hi, xy = isl_off[i]
    q = (np.asarray(uv) - lo) * isl_scale
    if rot[i]:
        q = q @ R90.T + np.array([(hi - lo)[1] * isl_scale, 0.0])
    return q + xy


report['relocated_scale'] = round(isl_scale, 3)
report['relocated_rotated'] = int(sum(rot.values()))
print('ISLANDS', len(dims), 'scale', isl_scale, 'rotated', sum(rot.values()))
for f in bm.faces:
    if f[bag_l]:
        continue
    t = f[oldf_l] - 1
    assert t >= 0, 'old face lost'
    for l in f.loops:
        u, v = l[uv_l].uv
        if t in isl_of:
            l[uv_l].uv = tuple(isl_map(isl_of[t], [u, v]))
        else:
            l[uv_l].uv = (u, v * VSCALE)
    if t in isl_of:
        f[rel_l] = isl_of[t] + 1
        reloc.append({'face_old': int(t), 'island': isl_of[t], 'uv_old': UV[t].round(7).tolist(),
                      'uv_new': isl_map(isl_of[t], UV[t]).round(7).tolist(), 'xyz': V[F[t]].round(6).tolist()})
report['relocated'] = reloc
report['islands'] = len(islands)
bm.faces.layers.int.remove(bm.faces.layers.int['old_face'])
bm.to_mesh(me)
me.update()
bm.free()
nt = len(me.polygons)
report['triangles'] = {'before': int(len(F)), 'after': nt,
                       'cavity_bag': int(sum(1 for p in me.polygons if me.attributes['mouth_bag'].data[p.index].value))}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('HEADFIX ' + json.dumps({k: report[k] for k in ('overlap', 'triangles', 'pieces')}))
print('CAVITY ' + json.dumps(report['cavity']))
