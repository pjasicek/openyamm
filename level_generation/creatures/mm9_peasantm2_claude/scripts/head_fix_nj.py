"""Repair the prepared Meshy head (work/head_v1.blend from head_prep_nj.py), head-local metres, crown at z = 0.15.
- Face (superseded, see the face section): Meshy left inner pockets behind the eyes and mouth (one 152-edge ring, non-manifold seam edges) and pin holes at the chin and
  jaw. Faces from which no ray escapes (64 directions over the normal hemisphere, none steeper than 35 deg below the horizon, so the
  neck opening does not count) are deleted, then rings under 1.6 cm close by a fan. Light Laplacian on the face away from the eye rims.
- Eyes: Meshy's eyeballs carry a lumpy iris; each becomes a fitted sphere (least squares), painted later.
- Hair: Meshy's helmet had a dozen tears and two layers at the fringe. Rebuilt as a polar grid about a point in the skull: per
  direction the outer radius of Meshy's hair (first hit from outside), holes filled, low-passed; per azimuth the lower edge where
  Meshy's hair ends (the fringe at the front, the jaw line at the sides, the nape behind). The rim turns in to a lip 3 mm inside the
  face skin and runs 2 cm up under the hair, so the edge reads solid from below.
Args: <in blend> <out blend> <report json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT, REP = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
rep = {}
face, hair, eyes = (bpy.data.objects[n] for n in ('Face', 'Hair', 'Eyes'))
rng = np.random.default_rng(1)


def fib(n):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n); th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)]


def boundary_comps(bm):
    seen = set(); comps = []
    for e in [e for e in bm.edges if e.is_boundary]:
        if e in seen: continue
        st = [e]; seen.add(e); cur = []
        while st:
            x = st.pop(); cur.append(x)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y not in seen: seen.add(y); st.append(y)
        comps.append(cur)
    return comps


EYES_SRC = eyes.data.copy()
# ---------------------------------------------------------------- eyes -> spheres (superseded: the eyes are skin now, see below)
bm = bmesh.new(); bm.from_mesh(eyes.data)
E = np.array([v.co[:] for v in bm.verts]); bm.free()
spheres = []
for side in (-1, 1):
    q = E[np.sign(E[:, 0]) == side]
    A = np.c_[2 * q, np.ones(len(q))]; b = (q ** 2).sum(1)
    sol = np.linalg.lstsq(A, b, rcond=None)[0]; c = sol[:3]; r = math.sqrt(sol[3] + c @ c)
    spheres.append((c, r))
rep['eyes'] = [[c.round(4).tolist(), round(r, 4)] for c, r in spheres]
# Meshy's eye pieces are oversized caps (2.6 cm across): an eyeball (r 1.4 cm, so it fills Meshy's lid-less opening) whose front sits at the cap's front
r_eye = 0.014; cy = E[:, 1].min() + r_eye + 0.001; cz = 0.5 * (spheres[0][0][2] + spheres[1][0][2])
cx = 0.5 * (abs(spheres[0][0][0]) + abs(spheres[1][0][0]))
bm = bmesh.new()
for side in (-1, 1):
    m = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r_eye)
    for v in m['verts']:                       # pole (z) turned to look forward (-y), then to the socket
        x, y, z = v.co
        v.co = Vector((x + side * cx, -z + cy, y + cz))
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(eyes.data); bm.free()
for p in eyes.data.polygons: p.use_smooth = True

# ---------------------------------------------------------------- face: a clean balloon shrunk onto Meshy's skin
# Meshy's face shell has inner pockets behind the eyes and mouth joined to the skin through slits, folds and islands wound the
# other way. Tried and dropped: visibility culling, island votes, fold relaxing, a raw polar resample (noisy), a voxel remesh
# (leaked). Route of mm9_bigfoot_claude/scripts/head_close.py: a smooth closed balloon (polar grid of Meshy's outer radius, the
# max over five jittered rays per cell, heavily low-passed) is relaxed and projected on the nearest point of Meshy's skin and eye
# caps in turns, decimated symmetric, and despiked. The eyes are skin, painted (as MM9's); ears merge under the hair.
SRCM = face.data.copy()
sb = bmesh.new(); sb.from_mesh(SRCM); sb.from_mesh(EYES_SRC); sbvh = BVHTree.FromBMesh(sb)
CF = np.array([0.0, 0.005, -0.02])
NAF, NEF = 120, 90
azf = np.linspace(0, 2 * np.pi, NAF, endpoint=False); elf = np.linspace(0, np.radians(165), NEF)
da, de = azf[1] - azf[0], elf[1] - elf[0]
RF = np.full((NEF, NAF), np.nan)
for i, e in enumerate(elf):
    for j, a_ in enumerate(azf):
        best = None
        for oe, oa in ((0, 0), (0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)):
            ee, aa = e + oe * de, a_ + oa * da
            d = np.array([np.sin(ee) * np.cos(aa), np.sin(ee) * np.sin(aa), np.cos(ee)])
            loc, nrm, idx, dist = sbvh.ray_cast(Vector(CF + d * 0.4), Vector(-d), 0.4)
            if idx is not None and (best is None or 0.4 - dist > best): best = 0.4 - dist
        if best is not None: RF[i, j] = best
hitrow = np.array([np.nonzero(~np.isnan(RF[:, j]))[0].max() for j in range(NAF)])
nlast = int(np.percentile(hitrow, 10)) - 1
RF = RF[:nlast + 1]; elf = elf[:nlast + 1]
for j in range(NAF):
    col = RF[:, j]; ok = ~np.isnan(col); RF[:, j] = np.interp(elf, elf[ok], col[ok])
def shifts(A):
    Ap = np.pad(A, ((1, 1), (0, 0)), mode='edge')
    return np.stack([np.roll(Ap, -dj, 1)[1 + di:1 + di + A.shape[0]] for di in (-1, 0, 1) for dj in (-1, 0, 1)])
w3 = np.array([0.25, 0.5, 0.25]); W9 = np.outer(w3, w3).ravel()
for _ in range(4): RF = np.tensordot(W9, shifts(RF), 1)
RF = 0.5 * (RF + RF[:, (NAF // 2 - np.arange(NAF)) % NAF])
bm = bmesh.new()
pole = bm.verts.new(Vector(CF + np.array([0, 0, RF[0].mean()])))
grid = []
for i in range(1, len(elf)):
    row = []
    for j, a_ in enumerate(azf):
        e = elf[i]; d = np.array([np.sin(e) * np.cos(a_), np.sin(e) * np.sin(a_), np.cos(e)])
        row.append(bm.verts.new(Vector(CF + d * RF[i, j])))
    grid.append(row)
for j in range(NAF):
    bm.faces.new((pole, grid[0][j], grid[0][(j + 1) % NAF]))
for i in range(len(grid) - 1):
    for j in range(NAF):
        a1, b1, c1, d1 = grid[i][j], grid[i + 1][j], grid[i + 1][(j + 1) % NAF], grid[i][(j + 1) % NAF]
        bm.faces.new((a1, b1, c1)); bm.faces.new((a1, c1, d1))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.faces.ensure_lookup_table()
if max(bm.faces, key=lambda f: f.calc_center_median().z).normal.z < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
rim = {v for e in bm.edges if e.is_boundary for v in e.verts}
far_hist = []
for it, (k, rel) in enumerate(((1.0, 3), (1.0, 2), (1.0, 2), (0.8, 1))):
    for _ in range(rel):
        nw = [(v, sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)) for v in bm.verts if v not in rim]
        for v, c in nw: v.co = v.co * 0.5 + c * 0.5
    far = 0
    for v in bm.verts:
        loc, nor, idx, dist = sbvh.find_nearest(v.co)
        if loc is not None and dist < 0.006: v.co = v.co.lerp(loc, k)
        else: far += 1
    far_hist.append(far)
rep['face_project_far'] = far_hist
for v in bm.verts:
    if abs(v.co.x) < 2e-4: v.co.x = 0
bm.to_mesh(face.data); bm.free(); sb.free()
bpy.context.view_layer.objects.active = face
for x in bpy.data.objects: x.select_set(x is face)
dmod = face.modifiers.new('D', 'DECIMATE'); dmod.ratio = 2600 / len(face.data.polygons); dmod.use_symmetry = True; dmod.symmetry_axis = 'X'; dmod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='D')
bm = bmesh.new(); bm.from_mesh(face.data)
desp = []
for r in range(6):
    bm.normal_update(); bad = []
    for v in bm.verts:
        if not v.link_edges or any(e.is_boundary for e in v.link_edges): continue
        c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        L = sum(e.calc_length() for e in v.link_edges) / len(v.link_edges)
        if (v.co - c).length > 0.45 * L or min(f.normal.dot(v.normal) for f in v.link_faces) < 0.2: bad.append((v, c))
    for v, c in bad: v.co = c
    desp.append(len(bad))
rep['face_despike'] = desp
rep['face_nonmanifold'] = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
bm.to_mesh(face.data); bm.free()
for p in face.data.polygons: p.use_smooth = True
bpy.data.objects.remove(eyes)

# ---------------------------------------------------------------- hair, polar grid
hb = bmesh.new(); hb.from_mesh(hair.data); hbvh = BVHTree.FromBMesh(hb)
fb = bmesh.new(); fb.from_mesh(face.data); fbvh = BVHTree.FromBMesh(fb)
H = np.array([v.co[:] for v in hb.verts])
C = np.array([0.0, 0.01, 0.02])
NA, NE = 48, 40
az = np.linspace(0, 2 * np.pi, NA, endpoint=False)          # 0 = +x (figure's left), pi/2 = +y (back), 3pi/2 = -y (front)
el = np.linspace(0, np.radians(150), NE)                       # from the crown down
R = np.full((NE, NA), np.nan)
for i, e in enumerate(el):
    for j, a in enumerate(az):
        d = np.array([np.sin(e) * np.cos(a), np.sin(e) * np.sin(a), np.cos(e)])
        loc, nrm, idx, dist = hbvh.ray_cast(Vector(C + d * 0.4), Vector(-d), 0.4)
        if idx is not None: R[i, j] = 0.4 - dist
# lower edge per azimuth: the last elevation with a hit in a run from the crown
low = np.zeros(NA)
for j in range(NA):
    col = ~np.isnan(R[:, j]); k = 0
    while k + 1 < NE and (col[k + 1] or (k + 2 < NE and col[k + 2])): k += 1
    low[j] = el[k]
rep['hair_low_deg_raw'] = np.degrees(low[::6]).round(1).tolist()
# fill gaps (tears) along the column, then low-pass radius and edge (wrap in azimuth)
for j in range(NA):
    col = R[:, j]; ok = ~np.isnan(col)
    R[:, j] = np.interp(el, el[ok], col[ok])
# Meshy's helmet stands up to 4 cm off the skull at the back (an egg, a mushroom from the front); MM9's bob lies close. Thickness
# over the skin along each ray is held to 0.6-2.0 cm
SK = np.full_like(R, np.nan)
for i, e in enumerate(el):
    for j, a in enumerate(az):
        d = np.array([np.sin(e) * np.cos(a), np.sin(e) * np.sin(a), np.cos(e)])
        loc, nrm, idx, dist = fbvh.ray_cast(Vector(C + d * 0.4), Vector(-d), 0.4)
        if idx is not None: SK[i, j] = 0.4 - dist
okk = ~np.isnan(SK)
rep['hair_thickness_cm_before'] = [round(float(np.percentile((R - SK)[okk], q)) * 100, 2) for q in (5, 50, 95)]
R[okk] = SK[okk] + np.clip(R[okk] - SK[okk], 0.006, 0.02)


def blur_az(x, s):
    k = np.exp(-0.5 * (np.arange(-3 * s, 3 * s + 1) / s) ** 2); k /= k.sum()
    pad = np.concatenate([x[-3 * s:], x, x[:3 * s]]); return np.convolve(pad, k, 'same')[3 * s:-3 * s]


low = blur_az(low, 2)
for i in range(NE): R[i] = blur_az(R[i], 1)
for j in range(NA):
    R[:, j] = np.convolve(np.pad(R[:, j], 2, mode='edge'), np.ones(5) / 5, 'same')[2:-2]
# rows: crown pole + NR rows down to each azimuth's edge
NR = 16
bm = bmesh.new()
pole = bm.verts.new(Vector(C + np.array([0, 0, np.interp(0, el, R[:, 0])])))
rows = []
for r in range(1, NR + 1):
    row = []
    for j, a in enumerate(az):
        e = low[j] * r / NR
        rad = np.interp(e, el, R[:, j])
        d = np.array([np.sin(e) * np.cos(a), np.sin(e) * np.sin(a), np.cos(e)])
        row.append(bm.verts.new(Vector(C + d * rad)))
    rows.append(row)
# lip: in to 3 mm inside the face skin at the edge, then 2 cm up under the hair
def skin_r(e, a):
    d = np.array([np.sin(e) * np.cos(a), np.sin(e) * np.sin(a), np.cos(e)])
    loc, nrm, idx, dist = fbvh.ray_cast(Vector(C + d * 0.4), Vector(-d), 0.4)
    return (0.4 - dist) if idx is not None else None, d
for k, back in enumerate((0.0, 0.08, 0.2)):
    row = []
    for j, a in enumerate(az):
        e = max(low[j] - back, 0.05)
        sr, d = skin_r(e, a)
        hr = np.interp(e, el, R[:, j])
        rad = min(hr - 0.004, sr - 0.003) if sr is not None else hr - 0.012
        row.append(bm.verts.new(Vector(C + d * rad)))
    rows.append(row)
for j in range(NA):
    bm.faces.new((pole, rows[0][(j + 1) % NA], rows[0][j]))
for r in range(len(rows) - 1):
    for j in range(NA):
        a_, b_, c_, d_ = rows[r][j], rows[r][(j + 1) % NA], rows[r + 1][(j + 1) % NA], rows[r + 1][j]
        bm.faces.new((a_, b_, c_)); bm.faces.new((a_, c_, d_))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# outward test: the crown faces point up
bm.faces.ensure_lookup_table()
top = max(bm.faces, key=lambda f: f.calc_center_median().z)
if top.normal.z < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
bm.to_mesh(hair.data); bm.free(); hb.free(); fb.free()
for p in hair.data.polygons: p.use_smooth = True
rep['hair_tris'] = len(hair.data.polygons); rep['hair_low_deg'] = np.degrees(low[::6]).round(1).tolist()
rep['tris'] = {o.name: len(o.data.polygons) for o in (face, hair)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=0)
print('HEADFIX', json.dumps(rep)[:1500])
