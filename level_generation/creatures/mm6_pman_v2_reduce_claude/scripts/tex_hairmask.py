"""Hairline review fix: for every face/neck skin texel (head set, piece 1) whether the hair mesh (piece 2) covers it
(a ray along the skin normal hits the hair within 4 cm) and its distance to the hair surface.
Out: work/hair_cover.npz (covered, distance; -1 where not skin)."""
import bpy, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
b = bpy.data.objects['Body']; me = b.data; pc = [a.value for a in me.attributes['piece'].data]
verts = [b.matrix_world @ v.co for v in me.vertices]
hair = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in me.polygons if pc[p.vertices[0]] == 2])
d = dict(np.load(os.path.join(HERE, 'work', 'uvraster_HeadUV.npz'))); skin = d['coverage'] & (d['piece'] == 1)  # loaded once
POS, NRM = d['pos'], d['normal']
covered = np.zeros(skin.shape, bool); dist = np.full(skin.shape, -1.0, np.float32)
for iy, ix in zip(*np.nonzero(skin)):
    p = Vector(POS[iy, ix]); n = Vector(NRM[iy, ix])
    hit = hair.ray_cast(p + n * .0005, n, .04)
    covered[iy, ix] = hit[0] is not None
    dist[iy, ix] = hair.find_nearest(p)[3]
np.savez_compressed(os.path.join(HERE, 'work', 'hair_cover.npz'), covered=covered, distance=dist)
print('HAIR COVER skin texels', int(skin.sum()), 'covered', int(covered.sum()), 'within 5 mm', int(((dist >= 0) & (dist < .005)).sum()))
