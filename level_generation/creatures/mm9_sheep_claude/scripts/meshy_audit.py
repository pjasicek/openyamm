"""Meshy return audit: boundary / non-manifold edges, edge-length outliers (threads), self-intersections (BVH).
Args: <glb>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
o = next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.faces.ensure_lookup_table()
L = np.array([e.calc_length() for e in bm.edges])
med = np.median(L)
long = [e for e in bm.edges if e.calc_length() > 6 * med]
bound = sum(1 for e in bm.edges if len(e.link_faces) == 1)
nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
bvh = BVHTree.FromBMesh(bm)
pairs = bvh.overlap(bvh)
inter = len([p for p in pairs if p[0] < p[1] and not set(bm.faces[p[0]].verts) & set(bm.faces[p[1]].verts)])
ip = [p for p in pairs if p[0] < p[1] and not set(bm.faces[p[0]].verts) & set(bm.faces[p[1]].verts)]
C = np.array([tuple(bm.faces[p[0]].calc_center_median()) for p in ip]) if ip else np.zeros((0, 3))
B = np.array([tuple((e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if len(e.link_faces) == 1])
def clusters(X):
    out = []
    used = np.zeros(len(X), bool)
    for i in range(len(X)):
        if used[i]: continue
        m = np.linalg.norm(X - X[i], axis=1) < 0.04
        used |= m
        out.append([int(m.sum())] + [round(v, 3) for v in X[m].mean(0)])
    return sorted(out, reverse=True)[:10]
print('INTER_CLUSTERS', clusters(C))
print('BOUND_CLUSTERS', clusters(B))
print('AUDIT ' + json.dumps({'edges': len(L), 'median_edge': float(med), 'long_edges': len(long),
      'long_edge_faces': len(set(f.index for e in long for f in e.link_faces)),
      'long_examples': [[round(x, 3) for x in e.verts[0].co] + [round(e.calc_length(), 3)] for e in long[:6]],
      'boundary': bound, 'nonmanifold': nonman, 'self_intersect_pairs': inter}))
