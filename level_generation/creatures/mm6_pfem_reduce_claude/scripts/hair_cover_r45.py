"""Hairline (round-2 review, after mm6_pman_v2_reduce_claude/scripts/tex_hairmask.py): for every head-set skin texel,
whether the hair or circlet mesh covers it (ray along the skin normal hits it within 4 cm), whether the braid
covers it, and its distance to the nearest hair/circlet surface. Out: work/hair_cover_r45.npz."""
import bpy, json, os, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
me = bpy.data.objects['Peasant'].data
part = [a.value for a in me.attributes['part'].data]
verts = [v.co.copy() for v in me.vertices]
tree = lambda names: BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in me.polygons if PARTS[part[p.index]] in names])
hair, braid = tree(('Hair', 'Headband')), tree(('Braid',))
d = np.load(os.path.join(HERE, 'work', 'uv3d_head.npz'))
SIZE = 1024
uv, xyz, tp = d['uv'], d['xyz'], d['part']
n = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
part_map = np.full((SIZE, SIZE), -1, np.int32); pos = np.zeros((SIZE, SIZE, 3), np.float32); nrm = np.zeros((SIZE, SIZE, 3), np.float32)
for t in range(len(uv)):
    p = uv[t] * SIZE; p[:, 1] = SIZE - p[:, 1]
    x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, SIZE - 1), min(y1, SIZE - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = p; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den; w2 = 1 - w0 - w1
    ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0); ys, xs = np.nonzero(ins)
    part_map[y0 + ys, x0 + xs] = tp[t]; nrm[y0 + ys, x0 + xs] = n[t]
    pos[y0 + ys, x0 + xs] = w0[ins, None] * xyz[t][0] + w1[ins, None] * xyz[t][1] + w2[ins, None] * xyz[t][2]
skin = part_map == PARTS.index('Body')
covered = np.zeros(skin.shape, bool); under_braid = np.zeros(skin.shape, bool); dist = np.full(skin.shape, -1.0, np.float32)
for iy, ix in zip(*np.nonzero(skin)):
    p = Vector(pos[iy, ix]); nn = Vector(nrm[iy, ix])
    covered[iy, ix] = hair.ray_cast(p + nn * .0005, nn, .04)[0] is not None
    under_braid[iy, ix] = braid.ray_cast(p + nn * .0005, nn, .04)[0] is not None
    dist[iy, ix] = hair.find_nearest(p)[3]
np.savez_compressed(os.path.join(HERE, 'work', 'hair_cover_r45.npz'), covered=covered, under_braid=under_braid, distance=dist)
print('HAIR COVER skin', int(skin.sum()), 'covered', int(covered.sum()), 'under braid', int(under_braid.sum()),
      'within 4 mm', int(((dist >= 0) & (dist < .004) & ~covered).sum()))
