"""Mesh stats of a GLB/blend object: verts, faces, boundary/non-manifold edges, inconsistent-winding edges,
coincident vertex pairs. Args: <glb|blend> [object]"""
import bpy, bmesh, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
src = argv[0]
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
ob = bpy.data.objects[argv[1]] if len(argv) > 1 else next(o for o in bpy.data.objects if o.type == 'MESH')
bm = bmesh.new(); bm.from_mesh(ob.data)
bnd = sum(1 for e in bm.edges if e.is_boundary)
nm = sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
bad = 0
for e in bm.edges:
    if len(e.link_faces) == 2:
        a, b = e.link_faces
        # consistent winding: the edge runs in opposite directions in the two faces
        def dirn(f):
            vs = list(f.verts)
            i = vs.index(e.verts[0]); return vs[(i + 1) % len(vs)] == e.verts[1]
        if dirn(a) == dirn(b):
            bad += 1
co = np.array([tuple(v.co) for v in bm.verts])
q = np.round(co / 1e-5).astype(np.int64)
_, cnt = np.unique(q, axis=0, return_counts=True)
print('STATS ' + json.dumps({'verts': len(bm.verts), 'faces': len(bm.faces), 'boundary_edges': bnd, 'nonmanifold_edges': nm,
                             'flipped_edges': bad, 'coincident_extra': int((cnt - 1).sum()), 'mesh_objects': [o.name for o in bpy.data.objects if o.type == 'MESH']}))
import os
if os.environ.get('BND'):
    pts = np.array([tuple((e.verts[0].co + e.verts[1].co) / 2) for e in bm.edges if e.is_boundary or (not e.is_manifold)])
    if len(pts):
        print('BND x', np.round(np.percentile(np.abs(pts[:, 0]), [0, 50, 100]), 4).tolist(), 'sample', np.round(pts[:6], 3).tolist())
