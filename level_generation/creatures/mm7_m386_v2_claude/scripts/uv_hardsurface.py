"""Hard-surface UV layout for the robot (replaces Smart UV Project, which cut the 305 Meshy pieces into 3,340 islands
of about 5 x 5 texels at 2K and left the retexture blobby).

Charts: faces joined across edges flatter than SHARP degrees (non-manifold edges always cut), charts under MIN_AREA
merged into the neighbour with the longest shared border and a similar facing, then unwrapped (angle based, from
cleared UVs: Blender's unwrap also cuts where existing UVs disagree) and checked; a chart whose texels stretch or flip
is split in two and unwrapped again. Then even texel density,
Head / Jaw / Gun islands at DENSE x density (linear), axis-aligned packing at 2K with an 8-texel margin.

Usage (Blender): uv_hardsurface.py [src.blend] [dst.blend] [--stats-only]
  src default work/uv_master_smartuv.blend (the Smart UV master, kept as the rollback), dst work/uv_master.blend.
  Also writes texturing/robot_neutral_hs.glb (unrigged, no materials) for the Meshy retexture and
  review/uv_stats_<label>.json. --stats-only measures the source layout and writes nothing else.
Env: SHARP (deg, 180: start from whole pieces), MIN_AREA (cm^2, 6), ANG_MAX (1.35), SPREAD_MAX (0.25), DENSE (2.0),
LABEL (hs), PACK_ROT / PACK_SHAPE (CARDINAL / CONCAVE), XATLAS=<python with xatlas> packs with xatlas instead
(xatlas_pack.py; tested: 821 vs Blender's 813 texels per metre, so Blender's packer is the default).
Charts that fail ANG_MAX / SPREAD_MAX or flip are split in two along their strongest crease (two-seed region grow)."""
import bpy, bmesh, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
stats_only = '--stats-only' in argv
argv = [a for a in argv if not a.startswith('--')]
src = os.path.join(HERE, argv[0] if argv else 'work/uv_master_smartuv.blend')
dst = os.path.join(HERE, argv[1] if len(argv) > 1 else 'work/uv_master.blend')
SHARP = math.radians(float(os.environ.get('SHARP', 180)))
MIN_AREA = float(os.environ.get('MIN_AREA', 6)) * 1e-4
DENSE = float(os.environ.get('DENSE', 2.0))
ANG_MAX = float(os.environ.get('ANG_MAX', 1.35))  # chart's area-weighted mean angle distortion s1/s2
SPREAD_MAX = float(os.environ.get('SPREAD_MAX', 0.25))  # chart's area-weighted mean |log| texel density deviation
LABEL = os.environ.get('LABEL', 'hs')
ATLAS = 2048
MARGIN = 8 / ATLAS

bpy.ops.wm.open_mainfile(filepath=src)
obj = bpy.data.objects['Robot']; rig = bpy.data.objects['Robot_Rig']
action = rig.animation_data.action
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.objects.active = obj
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(obj.data)
bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.verify()
F = len(bm.faces)
TRIS = bm.calc_loop_triangles()
TF = np.array([t[0].face.index for t in TRIS])  # triangle -> face
P = np.array([[tuple(l.vert.co) for l in t] for t in TRIS], np.float64)
N = np.array([tuple(f.normal) for f in bm.faces], np.float64)
AF = np.array([f.calc_area() for f in bm.faces])  # face areas (charts work on faces)
A3 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1) / 2  # triangle areas (metrics)

# Faces mostly weighted to Head / Jaw / Gun get DENSE x texel density.
dense_groups = {obj.vertex_groups[n].index for n in ('Head', 'Jaw', 'Gun') if n in obj.vertex_groups}
vw = np.array([sum(g.weight for g in v.groups if g.group in dense_groups) for v in obj.data.vertices])
dense_f = np.array([vw[[v.index for v in f.verts]].mean() >= 0.5 for f in bm.faces])
dense_face = dense_f[TF]


def uv_array():
    return np.array([[tuple(l[uvl].uv) for l in t] for t in TRIS], np.float64)


def jacobian(U):
    """Per face singular values of the 3D -> UV map (s1 >= s2) and the sign of its determinant."""
    e1 = P[:, 1] - P[:, 0]; e2 = P[:, 2] - P[:, 0]
    x = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    n = np.cross(e1, e2); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    y = np.cross(n, x)
    Q = np.stack([np.stack([np.einsum('ij,ij->i', e1, x), np.einsum('ij,ij->i', e1, y)], 1),
                  np.stack([np.einsum('ij,ij->i', e2, x), np.einsum('ij,ij->i', e2, y)], 1)], 2)  # 2x2 cols q1 q2
    D = np.stack([U[:, 1] - U[:, 0], U[:, 2] - U[:, 0]], 2)
    ok = np.abs(np.linalg.det(Q)) > 1e-14
    J = np.zeros((len(TRIS), 2, 2))
    J[ok] = D[ok] @ np.linalg.inv(Q[ok])
    s = np.linalg.svd(J, compute_uv=False)
    return s[:, 0], s[:, 1], np.sign(np.linalg.det(J)), ok


def islands_of(U):
    """UV islands: faces joined across an edge whose UVs agree on both sides."""
    parent = np.arange(F)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in bm.edges:
        if len(e.link_loops) != 2:
            continue
        a, b = e.link_loops
        ka = {tuple(np.round(a[uvl].uv, 6)), tuple(np.round(a.link_loop_next[uvl].uv, 6))}
        kb = {tuple(np.round(b[uvl].uv, 6)), tuple(np.round(b.link_loop_next[uvl].uv, 6))}
        if ka == kb:
            ra, rb = find(a.face.index), find(b.face.index)
            if ra != rb:
                parent[ra] = rb
    return np.array([find(i) for i in range(F)])


def measure(label):
    U = uv_array()
    s1, s2, sign, ok = jacobian(U)
    isl = islands_of(U)[TF]
    ids, inv = np.unique(isl, return_inverse=True)
    uva = np.abs(np.cross(U[:, 1] - U[:, 0], U[:, 2] - U[:, 0])) / 2
    px = np.bincount(inv, uva) * ATLAS * ATLAS
    area3 = np.bincount(inv, A3)
    dens = np.sqrt(uva / np.maximum(A3, 1e-12)) * ATLAS  # texels per metre
    normal = ~dense_face & ok & (A3 > 1e-9)
    ref = np.median(dens[normal])
    angle = s1 / np.maximum(s2, 1e-12)
    w = A3 / A3.sum()
    flips = 0
    for i in range(len(ids)):
        m = inv == i
        maj = np.sign((sign[m] * A3[m]).sum())
        flips += int(((sign[m] != maj) & (A3[m] > 1e-9)).sum())
    rel = dens[normal] / ref
    stats = dict(label=label, faces=F, islands=int(len(ids)),
                 island_px=dict(p10=float(np.percentile(px, 10)), median=float(np.median(px)),
                                p90=float(np.percentile(px, 90))),
                 islands_under_100px=int((px < 100).sum()), islands_under_1024px=int((px < 1024).sum()),
                 surface_in_islands_over_32x32=float(area3[px >= 1024].sum() / A3.sum()),
                 atlas_fill=float(uva.sum()),
                 texels_per_m=dict(normal_median=float(ref),
                                   dense_median=float(np.median(dens[dense_face & ok])) if dense_face.any() else None),
                 density_spread_p5_p95=[float(np.percentile(rel, 5)), float(np.percentile(rel, 95))],
                 angle_distortion=dict(mean=float((angle * w).sum()), p95=float(np.percentile(angle[A3 > 1e-9], 95))),
                 flipped_faces=flips, dense_area_share=float(A3[dense_face].sum() / A3.sum()))
    print('UVSTATS', json.dumps(stats))
    return stats


if stats_only:
    st = measure(LABEL)
    bpy.ops.object.mode_set(mode='OBJECT')
    json.dump(st, open(os.path.join(HERE, f'review/uv_stats_{LABEL}.json'), 'w'), indent=2)
    raise SystemExit

# --- charts by sharp edges
parent = np.arange(F)


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i


edge_faces = []
for e in bm.edges:
    lf = e.link_faces
    if len(lf) == 2:
        a, b = lf[0].index, lf[1].index
        edge_faces.append((e.index, a, b, e.calc_length()))
        if e.calc_face_angle(math.pi) < SHARP:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
chart = np.array([find(i) for i in range(F)])


def merge_small(chart):
    """Merge charts under MIN_AREA into the neighbour with the longest border among those facing within 80 deg."""
    for _ in range(50):
        ids, inv = np.unique(chart, return_inverse=True)
        area = np.bincount(inv, AF)
        nrm = np.zeros((len(ids), 3))
        np.add.at(nrm, inv, N * AF[:, None])
        nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
        border = {}
        for _, a, b, L in edge_faces:
            ca, cb = inv[a], inv[b]
            if ca != cb:
                border[(ca, cb)] = border.get((ca, cb), 0) + L
                border[(cb, ca)] = border.get((cb, ca), 0) + L
        best = {}
        for (ca, cb), L in border.items():
            if area[ca] >= MIN_AREA or nrm[ca] @ nrm[cb] < math.cos(math.radians(80)):
                continue
            if ca not in best or L > best[ca][1]:
                best[ca] = (cb, L)
        if not best:
            break
        remap = np.arange(len(ids))
        done = set()
        for ca in sorted(best, key=lambda c: area[c]):
            cb = best[ca][0]
            if ca in done or cb in done:
                continue
            remap[ca] = cb; done.update((ca, cb))
        new = remap[inv]
        if (new == inv).all():
            break
        chart = new
    return np.unique(chart, return_inverse=True)[1]


def split_connected(chart):
    """Relabel so that every chart is edge-connected (a split by facing can leave two pieces)."""
    par = np.arange(F)

    def fd(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for _, a, b, _L in edge_faces:
        if chart[a] == chart[b]:
            ra, rb = fd(a), fd(b)
            if ra != rb:
                par[ra] = rb
    return np.unique([fd(i) for i in range(F)], return_inverse=True)[1]


def unwrap(chart):
    # Blender's unwrap also cuts where the existing UVs of an edge disagree (implicit seams), so start from one point.
    for f in bm.faces:
        for l in f.loops:
            l[uvl].uv = (0.0, 0.0)
    for e in bm.edges:
        lf = e.link_faces
        e.seam = bool(len(lf) != 2 or chart[lf[0].index] != chart[lf[1].index])
    for f in bm.faces:
        f.select = True
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=0.001)


def chart_quality(chart):
    U = uv_array()
    s1, s2, sign, ok = jacobian(U)
    dens = np.sqrt(s1 * s2)
    bad = []; reasons = []
    ct = chart[TF]
    for c in np.unique(chart):
        m = (ct == c) & ok & (A3 > 1e-9)
        if m.sum() < 2:
            continue
        w = A3[m] / A3[m].sum()
        ang = ((s1[m] / np.maximum(s2[m], 1e-12)) * w).sum()
        d = dens[m] / np.exp((np.log(np.maximum(dens[m], 1e-12)) * w).sum())
        spread = (np.abs(np.log(np.maximum(d, 1e-6))) * w).sum()
        maj = np.sign((sign[m] * A3[m]).sum())
        flip = (sign[m] != maj).sum()
        r = (ang > ANG_MAX, spread > SPREAD_MAX, flip > 0)
        if any(r):
            bad.append(c); reasons.append(r)
    if os.environ.get('DBG'):
        rs = np.array(reasons) if reasons else np.zeros((0, 3), bool)
        print('REASONS angle', int(rs[:, 0].sum()), 'spread', int(rs[:, 1].sum()), 'flip', int(rs[:, 2].sum()))
    return bad


ADJ = [[] for _ in range(F)]
for _e, _a, _b, _L in edge_faces:
    ADJ[_a].append(_b); ADJ[_b].append(_a)


def split_by_facing(chart, c):
    """Split chart c in two connected halves: grow two regions from its most opposed faces (Dijkstra over face
    adjacency, step cost = the bend between the faces), so the cut follows the strongest crease."""
    import heapq
    m = np.where(chart == c)[0]
    inside = set(m.tolist())
    n = N[m]
    i = int(m[np.argmax(((n - n.mean(0)) ** 2).sum(1))])
    j = int(m[np.argmin(n @ N[i])])
    if i == j:
        return chart
    owner = {}; heap = [(0.0, i, 0), (0.0, j, 1)]
    while heap:
        d, f, o = heapq.heappop(heap)
        if f in owner:
            continue
        owner[f] = o
        for g in ADJ[f]:
            if g in inside and g not in owner:
                bend = math.acos(max(-1.0, min(1.0, float(N[f] @ N[g]))))
                heapq.heappush(heap, (d + bend + 0.02, g, o))
    out = chart.copy()
    new_id = chart.max() + 1
    for f, o in owner.items():
        if o == 1:
            out[f] = new_id
    return out


chart = merge_small(chart)
print('CHARTS initial', len(np.unique(chart)))
for rnd in range(int(os.environ.get("ROUNDS", 24))):
    unwrap(chart)
    bad = chart_quality(chart)
    print('ROUND', rnd, 'charts', len(np.unique(chart)), 'bad', len(bad), 'uv islands', len(np.unique(islands_of(uv_array()))))
    if not bad:
        break
    for c in bad:
        if (chart == c).sum() >= 2:
            chart = split_by_facing(chart, c)
    chart = split_connected(chart)

# even density, dense groups, pack
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.average_islands_scale()
U = uv_array()
isl = islands_of(U)
for i in np.unique(isl):
    m = isl == i
    if (AF[m] * dense_f[m]).sum() < 0.5 * AF[m].sum():
        continue
    loops = [l for k in np.where(m)[0] for l in bm.faces[int(k)].loops]
    c = np.mean([tuple(l[uvl].uv) for l in loops], 0)
    for l in loops:
        l[uvl].uv = (c + (np.array(l[uvl].uv) - c) * DENSE).tolist()
bmesh.update_edit_mesh(obj.data)
bpy.ops.uv.select_all(action='SELECT')
if os.environ.get('XATLAS'):
    import subprocess
    U = uv_array()
    key = {}; pos = []; uvs = []; idx = []
    for t in TRIS:
        row = []
        for l in t:
            k = (l.vert.index, round(l[uvl].uv.x, 7), round(l[uvl].uv.y, 7))
            if k not in key:
                key[k] = len(pos); pos.append(tuple(l.vert.co)); uvs.append(tuple(l[uvl].uv))
            row.append(key[k])
        idx.append(row)
    tmp = os.path.join(HERE, 'work', f'xatlas_{LABEL}')
    pos = np.array(pos, np.float64); idx = np.array(idx, np.int64)
    # denser charts: scale their positions about the chart centre (xatlas sizes charts by 3D area)
    isl_f = islands_of(U)
    tri_isl = isl_f[TF]
    for i in np.unique(tri_isl):
        tm = tri_isl == i
        fm = isl_f == i
        if (AF[fm] * dense_f[fm]).sum() < 0.5 * AF[fm].sum():
            continue
        vs = np.unique(idx[tm])
        c = pos[vs].mean(0)
        pos[vs] = c + (pos[vs] - c) * DENSE
    np.savez(tmp + '_in.npz', pos=pos.astype(np.float32), uv=np.array(uvs, np.float32), idx=idx.astype(np.uint32))
    subprocess.run([os.environ['XATLAS'], '-I', os.path.join(HERE, 'scripts/xatlas_pack.py'), tmp + '_in.npz',
                    tmp + '_out.npz', str(ATLAS), str(int(os.environ.get('XPAD', 4)))], check=True)
    r = np.load(tmp + '_out.npz')
    # per triangle corner from xatlas' own index buffer (same triangle order)
    xi = np.asarray(r['idx']).reshape(-1, 3); xu = r['uvx']
    assert len(xi) == len(TRIS)
    for t, row in zip(TRIS, xi):
        for l, v in zip(t, row):
            l[uvl].uv = (float(xu[v][0]), float(xu[v][1]))
    bmesh.update_edit_mesh(obj.data)
    print('XATLAS util', r['utilization'], r['size'], r['tpu'])
else:
  bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, rotate_method=os.environ.get('PACK_ROT', 'CARDINAL'),
                          scale=True, merge_overlap=False, margin_method='FRACTION', margin=MARGIN, pin=False,
                          shape_method=os.environ.get('PACK_SHAPE', 'CONCAVE'))
st = measure(LABEL)
st.update(sharp_deg=math.degrees(SHARP), min_area_cm2=MIN_AREA * 1e4, dense=DENSE, margin_px=8, charts=int(len(np.unique(chart))))
bpy.ops.object.mode_set(mode='OBJECT')
json.dump(st, open(os.path.join(HERE, f'review/uv_stats_{LABEL}.json'), 'w'), indent=2)
if action is not None:
    rig.animation_data.action = action
bpy.ops.wm.save_as_mainfile(filepath=dst)
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
dup = obj.copy(); dup.data = obj.data.copy(); dup.modifiers.clear(); dup.parent = None
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', f'robot_neutral_{LABEL}.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE')
print('UVDONE', LABEL, dst)
