"""Which head-set skin texels can be seen: texels cast rays along
camera-like directions (24 azimuths x elevations -10..50 degrees, dot with the face normal > 0.15) against the whole rest-pose
peasant (hair, braid, circlet and the body itself). Exposure = fraction of escaping rays. Scalp under the hair
shell is not; the temples and cheeks beside hanging hair are. Out: work/exposure_r45.npz (fraction of escaping rays
per sampled texel of the 1024 head-set raster, every 3rd texel)."""
import os
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = bpy.data.objects['Peasant'].data
tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
d = np.load(os.path.join(HERE, 'work', 'uv3d_head.npz'))
xyz, part = d['xyz'], d['part']
# camera-like directions (towards where a viewer stands): a ring of 24 azimuths at elevations -10..50 degrees.
# Full-sphere rays called the forehead under the circlet hidden (most directions hit the circlet and the fringe),
# although it is plainly visible from the front.
az = np.radians(np.arange(0, 360, 15)); el = np.radians([-10, 10, 30, 50])
dirs = np.array([[np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)] for e in el for a in az])
# per texel (every 3rd texel of the head-set skin raster, the rest from the nearest sample): large skin triangles
# straddle the hairline, so a per-triangle answer was too coarse
SIZE, STEP = 1024, 3
tri = np.full((SIZE, SIZE), -1, np.int32); pos = np.zeros((SIZE, SIZE, 3), np.float32); nrm = np.zeros((SIZE, SIZE, 3), np.float32)
for t in range(len(xyz)):
    if part[t] != 0:
        continue
    p = d['uv'][t] * SIZE; p[:, 1] = SIZE - p[:, 1]
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
    nn = np.cross(xyz[t][1] - xyz[t][0], xyz[t][2] - xyz[t][0]); nn /= max(np.linalg.norm(nn), 1e-12)
    tri[y0 + ys, x0 + xs] = t; nrm[y0 + ys, x0 + xs] = nn
    pos[y0 + ys, x0 + xs] = w0[ins, None] * xyz[t][0] + w1[ins, None] * xyz[t][1] + w2[ins, None] * xyz[t][2]
skin = tri >= 0
sample = skin & (np.add.outer(np.arange(SIZE) % STEP, np.arange(SIZE) % STEP) == 0)
exposure = np.zeros((SIZE, SIZE), np.float32)
D = [Vector(x) for x in dirs]
for iy, ix in zip(*np.nonzero(sample)):
    nn = Vector(nrm[iy, ix]); o = Vector(pos[iy, ix]) + nn * .0008
    use = [dv for dv in D if dv.dot(nn) > .15]
    exposure[iy, ix] = sum(tree.ray_cast(o, dv, .5)[0] is None for dv in use) / max(len(use), 1)
# Blender has no scipy: unify_skin.py fills the texels between samples from the nearest sample
np.savez_compressed(os.path.join(HERE, 'work', 'exposure_r45.npz'), exposure=exposure, sample=sample, skin=skin)
print('EXPOSURE skin texels', int(skin.sum()), 'samples', int(sample.sum()), 'hidden samples (<5 %)',
      int((sample & (exposure < .05)).sum()), 'visible samples', int((sample & (exposure >= .05)).sum()))
