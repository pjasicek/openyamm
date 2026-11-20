"""Rest-mesh audit of the wolf 'Body' (piece 0 = the skin): boundary and non-manifold edges, connected components,
self-intersecting face pairs (BVH overlap, faces sharing a vertex ignored) and folded faces, optionally inside a box.
Writes a JSON report and an npz of flagged vertex positions (Blender world) for fold_views.py MARK.

Args: <blend> <report json> <marks npz> [x0,x1,y0,y1,z0,z1]
"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
box = [float(v) for v in argv[3].split(',')] if len(argv) > 3 else None
body = bpy.data.objects['Body']
me = body.data
piece = np.array([d.value for d in me.attributes['piece'].data])
bm = bmesh.new()
bm.from_mesh(me)
bm.transform(body.matrix_world)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
faces = [f for f in bm.faces if all(piece[v.index] == 0 for v in f.verts)]
fset = set(f.index for f in faces)


def inbox(co):
    return box is None or (box[0] < co.x < box[1] and box[2] < co.y < box[3] and box[4] < co.z < box[5])


boundary, nonman = [], []
for e in bm.edges:
    lf = [f for f in e.link_faces if f.index in fset]
    if not lf:
        continue
    c = (e.verts[0].co + e.verts[1].co) / 2
    if not inbox(c):
        continue
    if len(lf) == 1:
        boundary.append(e)
    elif len(lf) > 2:
        nonman.append(e)
# components of the skin
seen, comps = set(), []
for f in faces:
    if f.index in seen:
        continue
    st, comp = [f], []
    seen.add(f.index)
    while st:
        x = st.pop()
        comp.append(x.index)
        for e in x.edges:
            for y in e.link_faces:
                if y.index in fset and y.index not in seen:
                    seen.add(y.index)
                    st.append(y)
    comps.append(comp)
comps.sort(key=len, reverse=True)
# self intersections
verts = [v.co.copy() for v in bm.verts]
polys = [[v.index for v in f.verts] for f in faces]
tree = BVHTree.FromPolygons(verts, polys, all_triangles=False)
pairs = []
for a, b in tree.overlap(tree):
    if a >= b:
        continue
    fa, fb = faces[a], faces[b]
    if set(v.index for v in fa.verts) & set(v.index for v in fb.verts):
        continue
    if inbox(fa.calc_center_median()) or inbox(fb.calc_center_median()):
        pairs.append((fa.index, fb.index))
flag = set()
for e in boundary + nonman:
    flag.update(v.index for v in e.verts)
for a, b in pairs:
    flag.update(v.index for v in bm.faces[a].verts)
    flag.update(v.index for v in bm.faces[b].verts)
pts = np.array([tuple(bm.verts[i].co) for i in sorted(flag)]) if flag else np.zeros((0, 3))
np.savez(argv[2], pts=pts, inter=np.array([tuple(bm.faces[a].calc_center_median()) for a, _ in pairs]) if pairs
         else np.zeros((0, 3)), bnd=np.array([tuple((e.verts[0].co + e.verts[1].co) / 2) for e in boundary])
         if boundary else np.zeros((0, 3)))
rep = {'skin_faces': len(faces), 'components': [len(c) for c in comps[:8]], 'n_components': len(comps),
       'boundary_edges': len(boundary), 'nonmanifold_edges': len(nonman), 'intersecting_pairs': len(pairs),
       'intersect_centres_sample': [[round(x, 3) for x in bm.faces[a].calc_center_median()] for a, _ in pairs[:12]],
       'boundary_sample': [[round(x, 3) for x in (e.verts[0].co + e.verts[1].co) / 2] for e in boundary[:12]]}
json.dump(rep, open(argv[1], 'w'), indent=1)
print('AUDIT ' + json.dumps(rep))
