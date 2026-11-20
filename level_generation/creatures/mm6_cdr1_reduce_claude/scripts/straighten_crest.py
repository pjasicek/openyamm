"""Centre crest spike (part 2) straightened: the restored x2 shows a thin straight spike, the rebuild followed the old
curved one. Each ring of the tube (consecutive vertex blocks, as build_horns.py created them) moves onto the straight
line from its first ring to the apex, keeping its arc-length fraction; UVs are untouched (the Meshy textures use
them). In/out: work/uv_master.blend."""
import os
import bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
me = bpy.data.objects['Body'].data
pf = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', pf)
vs = sorted({v for f in me.polygons if pf[f.index] == 2 for v in f.vertices})
SIDES = 6
co = np.array([me.vertices[i].co[:] for i in vs])
nring = (len(vs) - 2) // SIDES
assert nring * SIDES + 2 == len(vs), len(vs)
rings = co[:nring * SIDES].reshape(nring, SIDES, 3); apex = co[nring * SIDES]
centres = rings.mean(1); pts = np.vstack([centres, apex])
arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); frac = arc / arc[-1]
target = centres[0] + np.outer(frac[:-1], apex - centres[0])
for k in range(nring):
    for j in range(SIDES):
        me.vertices[vs[k * SIDES + j]].co = rings[k, j] + (target[k] - centres[k])
bottom = vs[-1]
print('STRAIGHTENED crest rings', nring, 'max move mm', round(float(np.linalg.norm(target - centres, axis=1).max()) * 1000, 1))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
