"""Thin-sheet audit of the wolf skin: for each skin vertex cast a ray inward (against the vertex normal) and report
the distance to the first skin hit (local thickness), and outward to the next wall (crevice width, 'gap'). Fins and overlapping sheets (fused fur layers folded into the
skin) have a thickness far below the body's. Args: <blend> <out npz> -> co, thick, normal (Blender world)."""
import bpy, bmesh, sys
import numpy as np
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
body = bpy.data.objects['Body']
me = body.data
piece = np.array([d.value for d in me.attributes['piece'].data])
bm = bmesh.new(); bm.from_mesh(me); bm.transform(body.matrix_world)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
skin = [f for f in bm.faces if all(piece[v.index] == 0 for v in f.verts)]
tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in skin])
co, th, nr, gap = [], [], [], []
for v in bm.verts:
    if piece[v.index] != 0:
        continue
    n = v.normal.normalized()
    hit = tree.ray_cast(v.co - n * 1e-4, -n, 2.0)
    co.append(tuple(v.co)); nr.append(tuple(n)); th.append(hit[3] if hit[0] is not None else 9.0)
    out = tree.ray_cast(v.co + n * 1e-4, n, 2.0)   # outward: another wall facing this one (crevice width)
    gap.append(out[3] if out[0] is not None else 9.0)
np.savez(argv[1], co=np.array(co), thick=np.array(th), normal=np.array(nr), gap=np.array(gap))
th = np.array(th)
print('THIN', len(th), 'thick<0.01', int((th < 0.01).sum()), '<0.02', int((th < 0.02).sum()), '<0.04', int((th < 0.04).sum()))
