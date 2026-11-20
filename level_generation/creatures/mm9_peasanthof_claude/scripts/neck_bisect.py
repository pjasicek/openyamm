"""Cut the one-shell body level at the head-set seam (z = Z in the MM9 frame) before head_split.py, so the head/body
material seam is one clean line round the neck instead of a zig-zag of whole faces (PF1's lesson). Only faces within
R of the neck joint's vertical axis and within 4 cm of the plane are cut; weights and attributes interpolate.
Args: <in blend> <out blend> [Z 0.32] [R 0.16]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
Z = float(a[2]) if len(a) > 2 else 0.32
R = float(a[3]) if len(a) > 3 else 0.16
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
nc = rig.matrix_world @ rig.data.bones['Bip01 Neck'].head_local
mwi = ob.matrix_world.inverted()
bm = bmesh.new(); bm.from_mesh(ob.data)
mw = ob.matrix_world
geom = []
for f in bm.faces:
    ws = [mw @ v.co for v in f.verts]
    if all(abs(w.z - Z) < 0.04 and (Vector((w.x, w.y)) - Vector((nc.x, nc.y))).length < R for w in ws):
        geom.append(f)
edges = {e for f in geom for e in f.edges}; verts = {v for f in geom for v in f.verts}
co = mwi @ Vector((0, 0, Z)); no = (mwi.to_3x3().transposed().inverted() @ Vector((0, 0, 1))).normalized()
res = bmesh.ops.bisect_plane(bm, geom=list(verts) + list(edges) + geom, plane_co=co, plane_no=no)
bm.to_mesh(ob.data); ob.data.update()
print('NECKCUT faces', len(geom), 'new geom', len(res['geom_cut']), 'tris', sum(len(p.vertices) - 2 for p in ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
