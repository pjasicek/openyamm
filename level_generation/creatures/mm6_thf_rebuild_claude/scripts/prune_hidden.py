"""MM6 thief: delete skull, neck and face faces (parts 1, 2 above z 0.56) that no view can reach: for each face, rays from 0.4 mm above its centroid
along 96 directions of the hemisphere around its normal; a face is hidden when every ray meets another face within REACH.
The coif covers most of Meshy's face shell (Smart Topology kept the whole head under it). Textures and UVs of the kept faces
are untouched. Args: <in blend> <out blend> [reach m]"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[:2]; REACH = float(a[2]) if len(a) > 2 else 0.5
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
tree = BVHTree.FromBMesh(bm)
pl = bm.faces.layers.int['part']
k = np.arange(96) + 0.5; th = np.arccos(1 - k / 96); ph = math.pi * (1 + 5 ** 0.5) * k
D = np.c_[np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)]
hidden = []
for f in bm.faces:
    if f[pl] not in (1, 2) or f.calc_center_median().z < 0.56: continue
    n = f.normal; c = f.calc_center_median() + n * 0.0004
    t = n.orthogonal().normalized(); bvec = n.cross(t)
    seen = False
    for d in D:
        r = t * d[0] + bvec * d[1] + n * d[2]
        hit = tree.ray_cast(c, r, REACH)
        if hit[0] is None or hit[2] == f.index:
            seen = True; break
    if not seen: hidden.append(f)
print('HIDDEN face piece', len(hidden), 'of', 'neck, skull, face')
bmesh.ops.delete(bm, geom=hidden, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('PRUNE', len(me.polygons), 'tris')
