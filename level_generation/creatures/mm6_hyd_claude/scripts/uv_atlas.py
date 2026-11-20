"""UVs for the hydra's two texture sets (one 'UVMap' layer; each face's material picks the texture):
  body texture 2048x2048: body and necks (part 0), filling 0..1,
  head texture 1536x1024: one 512x512 tile per head (part k; tile column (k-1)%3, row (k-1)//3 from the top; the
  sixth tile is unused), k = 1..5 left to right in the front view.
Parts: the face attribute 'part' written by graft_heads.py (0 body, k head k); without it (an ungrafted mesh), the
flood fill of hyd_parts.head_flood.
Body: tubes unwrapped analytically: u = angle round the face's chain x local radius, v = arc length, one strip per
chain, seam along the back of the necks and the underside of the body (angle-based unwrapping flattened closed tubes
into blobs). Faces the tube map distorts (the junction where the necks merge, the outer necks' runs along the ground,
far from any chain axis: singular-value ratio above MAX_ANISO, or flipped) are grown by JUNCTION_GROW rings and get
smart-projected islands instead (they showed as smeared streaks); only connected clusters of at least MIN_CLUSTER
flagged faces count (single slivers and spike tips are anisotropic by shape). Heads: smart projection at 66 degrees: on the Smart Topology heads it
measured 0-3% of the area stretched beyond 2:1 and all of it within 2x of the median texel density; normal-binned
charts unwrapped angle-based or conformally left 12-55% within 2x (work/tmp/uvtry.py).
Run on a rigged file (weights give each vertex its chain):
  blender --background work/rig_v1.blend --python scripts/uv_atlas.py -- <out.blend>
Writes <out.blend> (object 'Hydra', rig kept), work/atlas_uv_tris.npy, work/atlas_part.npy, review/uv_atlas.png."""
import bpy, bmesh, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hyd_parts
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEAD_BACK = 0.035
HEAD_TEX = (1536.0, 1024.0)                                   # head texture size; tiles of 512
TILE = 512.0
MARGIN = 0.004
MAX_ANISO, JUNCTION_GROW, MIN_CLUSTER = 2.2, 2, 15
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = args[0] if args else os.path.join(HERE, 'work', 'hd_atlas.blend')


def box_of(k):
    """(x, y, w, h) of part k in its own texture's pixels, y from the top."""
    if k == 0:
        return (0.0, 0.0, 2048.0, 2048.0), (2048.0, 2048.0)
    return (((k - 1) % 3) * TILE, ((k - 1) // 3) * TILE, TILE, TILE), HEAD_TEX

rig = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
chains = [{'names': c['names'], 'J': np.array(c['joints']), 'R': np.array(c['radius'])} for c in rig['chains']]
bone_chain = {nm: ci for ci, c in enumerate(chains) for nm in c['names']}
obj = bpy.data.objects['Hydra']; me = obj.data
co = np.array([tuple(v.co) for v in me.vertices])
group_name = {g.index: g.name for g in obj.vertex_groups}
owner = np.zeros(len(co), int)
for v in me.vertices:
    g = max(v.groups, key=lambda x: x.weight)
    owner[v.index] = bone_chain[group_name[g.group]]


def nearest_on_chain(ci, p):
    J = chains[ci]['J']; best = (1e9, 0, 0.0)
    for i in range(len(J) - 1):
        d = J[i + 1] - J[i]; t = float(np.clip((p - J[i]) @ d / (d @ d), 0, 1))
        dist = float(np.linalg.norm(p - (J[i] + t * d)))
        if dist < best[0]:
            best = (dist, i, t)
    return best[1], best[2]


# per chain and segment a frame carried along the chain (parallel transport): F = belly side for necks (front at the
# base), top for the body; theta is measured from F round the segment, and the seam runs at 180 degrees
frames = []
for ci, c in enumerate(chains):
    J = c['J']; T = [(J[i + 1] - J[i]) / np.linalg.norm(J[i + 1] - J[i]) for i in range(len(J) - 1)]
    ref = np.array([0, -1.0, 0]) if ci else np.array([0, 0, 1.0])
    F = ref - (ref @ T[0]) * T[0]; F /= np.linalg.norm(F); out = [F]
    for i in range(1, len(T)):
        F = F - (F @ T[i]) * T[i]; F /= np.linalg.norm(F); out.append(F)
    frames.append((T, out))
arc = np.zeros(len(co)); theta = np.zeros(len(co))
for v in range(len(co)):
    ci = owner[v]; J = chains[ci]['J']; i, t = nearest_on_chain(ci, co[v])
    L = np.linalg.norm(np.diff(J, axis=0), axis=1)
    arc[v] = L[:i].sum() + t * L[i]
    T, F = frames[ci][0][i], frames[ci][1][i]; S = np.cross(T, F)
    r = co[v] - (J[i] + t * (J[i + 1] - J[i]))
    theta[v] = math.atan2(float(r @ S), float(r @ F))
tube_cache = {}


def tube_coords(v, ci):
    """(theta, arc, local radius) of vertex v relative to chain ci."""
    key = (v, ci)
    if key not in tube_cache:
        J = chains[ci]['J']; i, t = nearest_on_chain(ci, co[v])
        L = np.linalg.norm(np.diff(J, axis=0), axis=1)
        T, F = frames[ci][0][i], frames[ci][1][i]; S = np.cross(T, F)
        r = co[v] - (J[i] + t * (J[i + 1] - J[i]))
        R = chains[ci]['R'][i] * (1 - t) + chains[ci]['R'][i + 1] * t
        tube_cache[key] = (math.atan2(float(r @ S), float(r @ F)), L[:i].sum() + t * L[i], max(R, 0.02))
    return tube_cache[key]


head_start = {ci: np.linalg.norm(np.diff(c['J'], axis=0), axis=1)[:-1].sum() for ci, c in enumerate(chains) if ci}
adj = [[] for _ in co]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
if 'part' in me.attributes and me.attributes['part'].domain == 'FACE':
    fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
    vpart = np.zeros(len(co), int)
    for p in me.polygons:
        if fp[p.index]:
            vpart[list(p.vertices)] = fp[p.index]
else:
    vpart = hyd_parts.head_flood(co, adj, rig['chains'], HEAD_BACK)

bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part_layer = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
fpart = {}
for f in bm.faces:
    parts = [int(vpart[v.index]) for v in f.verts]
    fpart[f] = max(set(parts), key=parts.count)
for _ in range(3):                              # no lone faces on either side of a head cut
    new = {}
    for f in bm.faces:
        votes = [fpart[g] for e in f.edges for g in e.link_faces if g is not f] + [fpart[f]]
        new[f] = max(set(votes), key=votes.count)
    fpart = new
for f in bm.faces:
    f[part_layer] = fpart[f]
# chain ownership per face (majority of its vertices, then smoothed over neighbours) so the borders between chains
# are clean lines without isolated faces
fown = {f: max(set(owner[[v.index for v in f.verts]]), key=list(owner[[v.index for v in f.verts]]).count) for f in bm.faces}
for _ in range(3):
    new = {}
    for f in bm.faces:
        votes = [fown[g] for e in f.edges for g in e.link_faces if g is not f] + [fown[f]] * 2
        new[f] = max(set(votes), key=votes.count)
    fown = new
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    faces = list(e.link_faces)
    border = len({f[part_layer] for f in faces}) > 1 or len({fown[f] for f in faces}) > 1
    # the shortest way round from theta a to theta b crosses the back (+-180 degrees)
    cut_tube = owner[a] == owner[b] and abs(theta[a] - theta[b]) > math.pi
    e.seam = bool(border or cut_tube)


def islands():
    seen = set(); out = []
    for f in bm.faces:
        if f in seen:
            continue
        stack = [f]; seen.add(f); island = []
        while stack:
            a = stack.pop(); island.append(a)
            for e in a.edges:
                if not e.seam:
                    for g in e.link_faces:
                        if g not in seen:
                            seen.add(g); stack.append(g)
        out.append(island)
    return out


# a small island left by a wiggle joins the neighbour it shares the longest seam with (same part only)
CRUMB = 12
for _ in range(5):
    small = [i for i in islands() if len(i) < CRUMB]
    if not small:
        break
    for island in small:
        members = set(island); shared = {}
        for f in island:
            for e in f.edges:
                if e.seam:
                    for g in e.link_faces:
                        if g not in members and g[part_layer] == f[part_layer]:
                            shared.setdefault(id_of := fown[g], []).append(e)
        if shared:
            for e in max(shared.values(), key=len):
                e.seam = False
print('ISLANDS', sorted(len(i) for i in islands())[-12:], 'total', len(islands()))
counts = np.bincount([f[part_layer] for f in bm.faces], minlength=6)
bm.faces.ensure_lookup_table()
face_owner = np.array([fown[bm.faces[i]] for i in range(len(bm.faces))])
bm.to_mesh(me); bm.free()
print('PART triangles', counts.tolist())

for layer in list(me.uv_layers):
    me.uv_layers.remove(layer)
me.uv_layers.new(name='Upload'); me.uv_layers.new(name='UVMap')
me.uv_layers.active = me.uv_layers['Upload']
for o in bpy.context.view_layer.objects:
    o.select_set(o is obj)
bpy.context.view_layer.objects.active = obj
bpy.context.scene.tool_settings.mesh_select_mode = (False, False, True)
bpy.context.scene.tool_settings.use_uv_select_sync = False
part_of = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part_of)


def select_part(k):
    """Edit mode with exactly part k's faces (and their vertices and edges) selected, UVs too."""
    if obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    bme = bmesh.from_edit_mesh(me); bme.faces.ensure_lookup_table()
    for f in bme.faces:
        f.select_set(False)
    for f in bme.faces:
        if part_of[f.index] == k:
            f.select_set(True)
    bme.select_flush_mode(); bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')


def box_aspect(box):
    return box[2] / box[3]


for k in range(6):
    box = box_of(k)[0]
    if not (part_of == k).any():
        continue
    select_part(k)
    if k == 0:
        # tubes: u = angle round the face's chain x local radius, v = distance along the chain (one strip per chain,
        # cut along the back seam); angle-based unwrapping flattened the closed tubes into blobs
        bpy.ops.object.mode_set(mode='OBJECT')
        uvd = me.uv_layers['Upload'].data
        for p in me.polygons:
            if part_of[p.index] != 0:
                continue
            ci = face_owner[p.index]
            tc = [tube_coords(me.loops[li].vertex_index, ci) for li in p.loop_indices]
            ths = [c[0] for c in tc]
            wrap = max(ths) - min(ths) > math.pi
            for li, (th, a_, R) in zip(p.loop_indices, tc):
                if wrap and th < 0:
                    th += 2 * math.pi
                uvd[li].uv = (th * R, a_)
        # faces the tube map distorts -> smart projection
        bad = set(); dets = {}; anis = {}
        for p in me.polygons:
            if part_of[p.index] != 0:
                continue
            P = [me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]
            U = [uvd[li].uv for li in p.loop_indices]
            e1, e2 = P[1] - P[0], P[2] - P[0]
            n = e1.cross(e2)
            if n.length < 1e-12:
                continue
            x = e1.normalized(); y = n.normalized().cross(x)
            A = np.array([[e1.dot(x), e2.dot(x)], [e1.dot(y), e2.dot(y)]])
            B = np.array([[U[1][0] - U[0][0], U[2][0] - U[0][0]], [U[1][1] - U[0][1], U[2][1] - U[0][1]]])
            M = B @ np.linalg.inv(A)
            sv = np.linalg.svd(M, compute_uv=False)
            dets[p.index] = np.linalg.det(M); anis[p.index] = sv[0] / max(sv[1], 1e-9)
        # the tube map is mirrored on some chains (harmless for a bake): a face is flipped only against its chain's
        # majority orientation
        sign = {}
        for f, d in dets.items():
            sign.setdefault(face_owner[f], []).append(np.sign(d))
        major = {c: np.sign(np.sum(v)) or 1.0 for c, v in sign.items()}
        bad = {f for f, d in dets.items() if np.sign(d) != major[face_owner[f]] or anis[f] > MAX_ANISO}
        print('ANISO pct', np.percentile(list(anis.values()), [50, 90, 99]).round(2), 'flagged before growing', len(bad))
        np.save(os.path.join(HERE, 'work', 'tmp', 'junction_seed.npy'), np.array(sorted(bad), int))
        vert_faces = {}
        for p in me.polygons:
            for v in p.vertices:
                vert_faces.setdefault(v, []).append(p.index)
        # keep connected clusters of at least MIN_CLUSTER flagged faces: single slivers and spike tips are anisotropic
        # by shape, the junction is a solid area
        edge_faces = {}
        for p in me.polygons:
            for ek in p.edge_keys:
                edge_faces.setdefault(ek, []).append(p.index)
        seen = set(); keep = set()
        for f in bad:
            if f in seen:
                continue
            stack = [f]; seen.add(f); cluster = []
            while stack:
                a_ = stack.pop(); cluster.append(a_)
                for ek in me.polygons[a_].edge_keys:
                    for g in edge_faces[ek]:
                        if g in bad and g not in seen:
                            seen.add(g); stack.append(g)
            if len(cluster) >= MIN_CLUSTER:
                keep.update(cluster)
        bad = keep
        for _ in range(JUNCTION_GROW):
            grow = set(bad)
            for f in bad:
                for v in me.polygons[f].vertices:
                    grow.update(g for g in vert_faces[v] if part_of[g] == 0)
            bad = grow
        print('JUNCTION faces smart-projected', len(bad))
        np.save(os.path.join(HERE, 'work', 'junction_faces.npy'), np.array(sorted(bad), int))
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bme = bmesh.from_edit_mesh(me); bme.faces.ensure_lookup_table()
        for f in bme.faces:
            f.select_set(f.index in bad)
        bme.select_flush_mode(); bmesh.update_edit_mesh(me)
        # angle-based unwrap of the junction, cut by the existing seams (tube back lines open the outer necks' ground
        # runs) and its own border; smart projection shattered this lumpy area into hundreds of tiny islands
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, margin=0.0)
        select_part(k)
    else:
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    # pre-apply the box aspect so the packed unit square maps onto the box without distorting islands
    uv = me.uv_layers['Upload'].data; a = box_aspect(box)
    for p in me.polygons:
        if part_of[p.index] == k:
            for li in p.loop_indices:
                u, v = uv[li].uv; uv[li].uv = (u / a, v) if a < 1 else (u, v * a)
    select_part(k)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(shape_method='CONCAVE', rotate=True, margin=MARGIN, scale=True)
    bpy.ops.object.mode_set(mode='OBJECT')

up = me.uv_layers['Upload'].data; at = me.uv_layers['UVMap'].data
coverage = {}
for p in me.polygons:
    (x, y, w, h), (TW, TH) = box_of(part_of[p.index])
    for li in p.loop_indices:
        u, v = up[li].uv
        at[li].uv = ((x + u * w) / TW, 1.0 - (y + (1.0 - v) * h) / TH)
me.uv_layers.active = me.uv_layers['UVMap']
me.uv_layers['UVMap'].active_render = True
me.uv_layers.remove(me.uv_layers['Upload'])
up = None

# layout review: atlas islands coloured by part, with per-part coverage of its box
from mathutils.geometry import area_tri
at = me.uv_layers['UVMap'].data
for k in range(6):
    area = 0.0
    for p in me.polygons:
        if part_of[p.index] == k:
            pts = [Vector((at[li].uv[0], at[li].uv[1], 0)) for li in p.loop_indices]
            area += area_tri(*pts[:3])
    (x, y, w, h), (TW, TH) = box_of(k)
    coverage[k] = round(area / (w * h / (TW * TH)), 3)
print('COVERAGE of each box', coverage)
json.dump({'parts': counts.tolist(), 'coverage': coverage}, open(os.path.join(HERE, 'work', 'uv_atlas.json'), 'w'))
np.save(os.path.join(HERE, 'work', 'atlas_uv_tris.npy'),
        np.array([[tuple(at[li].uv) for li in p.loop_indices] for p in me.polygons], np.float32))
np.save(os.path.join(HERE, 'work', 'atlas_part.npy'), part_of)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SAVED', OUT)
