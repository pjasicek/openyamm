"""Clean and symmetrise the Meshy Smart Topology return (from mm9_wolf_claude/scripts/clean_meshy.py).

Args: <meshy glb> <out glb> <voxel size, 0 = keep the Meshy surface> <keep side +1|-1> [report json]

1. Weld; the main component is the body, small separate pieces (eyes) are kept as returned.
2. Body: voxel remesh (uniform voxel quads, adaptivity 0) and a light smooth (factor 0.5, 4 iterations) where
   overlapping layers fuse (wolf lesson), unless the voxel size is 0.
3. Mirror plane: the yaw/roll/offset that best maps the body onto its own mirror image (grid search, mean nearest
   distance), applied to everything, so the creature's mid-plane is x = 0.
4. Symmetrise: keep the chosen half of the body and mirror it (bmesh symmetrize, seam welded at x = 0); the eye on
   the kept side is mirrored to replace the other one. MM9 bodies are exactly mirror-symmetric.
"""
import bpy, bmesh, sys, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, VOX, SIDE = argv[0], argv[1], float(argv[2]), int(argv[3])
REP = argv[4] if len(argv) > 4 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
src = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
seen, comps = set(), []
for v in bm.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
main = set(comps[0])
rep = {'components': [len(c) for c in comps]}


def make(name, keep):
    b2 = bm.copy(); b2.verts.ensure_lookup_table()
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if (v.index in main) != keep], context='VERTS')
    me = bpy.data.meshes.new(name); b2.to_mesh(me)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


body = make('Body', True)
pieces = make('Pieces', False)
for o in list(bpy.data.objects):
    if o not in (body, pieces):
        bpy.data.objects.remove(o)
rep['body_faces_before'] = len(body.data.polygons)
if VOX > 0:
    body.data.remesh_voxel_size = VOX
    body.data.remesh_voxel_adaptivity = 0.0
    bpy.context.view_layer.objects.active = body
    for o in bpy.data.objects:
        o.select_set(o == body)
    bpy.ops.object.voxel_remesh()
    sm = body.modifiers.new('smooth', 'SMOOTH'); sm.factor = 0.5; sm.iterations = 4
    bpy.ops.object.modifier_apply(modifier='smooth')
    rep['voxel_faces'] = len(body.data.polygons)

# ---- mirror plane
P = np.array([tuple(v.co) for v in body.data.vertices])
rng = np.random.default_rng(0)
S = P[rng.choice(len(P), min(4000, len(P)), replace=False)]
c0 = P.mean(0)


def score(yaw, roll, off):
    R = (Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(yaw, 3, 'Z'))
    R = np.array(R)
    Q = (S - c0) @ R.T
    Q[:, 0] -= off
    M = Q.copy(); M[:, 0] *= -1
    k = KDTree(len(Q))
    for i, q in enumerate(Q):
        k.insert(Vector(q), i)
    k.balance()
    return float(np.mean([k.find(Vector(m))[2] for m in M]))


best = (score(0, 0, 0), 0.0, 0.0, 0.0)
for step in (math.radians(1.0), math.radians(0.25)):
    for _ in range(3):
        _, y0, r0, o0 = best
        for dy in (-2, -1, 0, 1, 2):
            for dr in (-2, -1, 0, 1, 2):
                y, r = y0 + dy * step, r0 + dr * step
                R = np.array(Matrix.Rotation(r, 3, 'Y') @ Matrix.Rotation(y, 3, 'Z'))
                Q = (S - c0) @ R.T
                for off in np.linspace(o0 - 0.004, o0 + 0.004, 5):
                    s = score(y, r, off)
                    if s < best[0]:
                        best = (s, y, r, off)
rep['mirror'] = {'mean_dist_before': score(0, 0, 0), 'mean_dist_after': best[0],
                 'yaw_deg': math.degrees(best[1]), 'roll_deg': math.degrees(best[2]), 'offset': best[3]}
_, y, r, off = best
T = Matrix.Translation((-off, 0, 0)) @ (Matrix.Rotation(y, 4, 'Z').__class__(
    (Matrix.Rotation(r, 3, 'Y') @ Matrix.Rotation(y, 3, 'Z')).to_4x4())) @ Matrix.Translation(-Vector(c0))
T = Matrix.Translation(Vector((c0[0], 0, 0)) * 0) @ T
for o in (body, pieces):
    o.data.transform(T)
# keep the original centre height/length (only x is re-centred)
shift = Vector((0, c0[1], c0[2]))
for o in (body, pieces):
    o.data.transform(Matrix.Translation(shift))

# ---- symmetrise the body
b = bmesh.new(); b.from_mesh(body.data)
bmesh.ops.symmetrize(b, input=b.verts[:] + b.edges[:] + b.faces[:], direction='-X' if SIDE < 0 else 'X', dist=1e-4)
bmesh.ops.remove_doubles(b, verts=b.verts, dist=1e-5)
# small Meshy holes (a few boundary loops on the neck and flanks): fill loops of at most 16 edges
nb = sum(1 for e in b.edges if e.is_boundary)
bmesh.ops.holes_fill(b, edges=[e for e in b.edges if e.is_boundary], sides=16)
# pinholes that holes_fill leaves (bow-tie loops of 2-8 edges): merge each loop's vertices into its centroid
for _ in range(3):
    seen_e, small = set(), []
    for e in b.edges:
        if not e.is_boundary or e.index in seen_e:
            continue
        st, L = [e], set()
        seen_e.add(e.index)
        while st:
            x = st.pop(); L.update(x.verts)
            for v in x.verts:
                for y in v.link_edges:
                    if y.is_boundary and y.index not in seen_e:
                        seen_e.add(y.index); st.append(y)
        if len(L) <= 8:
            small.append(list(L))
    if not small:
        break
    for L in small:
        if all(v.is_valid for v in L):
            bmesh.ops.pointmerge(b, verts=L, merge_co=sum((v.co for v in L), Vector()) / len(L))
    b.edges.index_update(); b.verts.index_update()
bmesh.ops.dissolve_degenerate(b, dist=1e-6, edges=b.edges[:])
bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 4])
rep['body_boundary_edges'] = [nb, sum(1 for e in b.edges if e.is_boundary)]
loops, seen_e = [], set()
for e in b.edges:
    if not e.is_boundary or e.index in seen_e:
        continue
    st, L = [e], []
    seen_e.add(e.index)
    while st:
        x = st.pop(); L.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen_e:
                    seen_e.add(y.index); st.append(y)
    c = sum((x.verts[0].co for x in L), Vector()) / len(L)
    loops.append([len(L), [round(t, 3) for t in c]])
rep['open_loops'] = loops
b.to_mesh(body.data); b.free()
# ---- eyes: keep the piece(s) on the kept side and mirror them
b = bmesh.new(); b.from_mesh(pieces.data); b.verts.ensure_lookup_table()
seen, pcs = set(), []
for v in b.verts:
    if v.index in seen:
        continue
    c, st = [], [v]; seen.add(v.index)
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen:
                seen.add(w.index); st.append(w)
    pcs.append(c)
drop = [v for c in pcs if np.sign(np.mean([v.co.x for v in c])) != SIDE for v in c]
bmesh.ops.delete(b, geom=drop, context='VERTS')
dup = bmesh.ops.duplicate(b, geom=b.verts[:] + b.edges[:] + b.faces[:])
nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in nv:
    v.co.x = -v.co.x
bmesh.ops.reverse_faces(b, faces=[g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)])
b.to_mesh(pieces.data); b.free()
rep['eye_pieces_kept'] = len(pcs) - len(set(id(c) for c in pcs if any(v in drop for v in c)))
for o in (body, pieces):
    for p in o.data.polygons:
        p.use_smooth = True
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.data.update()
rep['faces_after'] = len(body.data.polygons)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
if REP:
    json.dump(rep, open(REP, 'w'), indent=1)
print('CLEAN ' + json.dumps(rep))
