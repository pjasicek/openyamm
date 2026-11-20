"""Close the seams the reshape smoothing opened (positions only): vertices that coincided in the ORIGINAL master (< 1e-5 m;
Meshy's split seams, held together only by position) take the mean of their reshaped positions again. Writes the total
move from the original as <out>_move.npy ([co_orig | move]) for move_upload.py.
Args: -- <original blend> <reshaped blend> <out blend>"""
import bpy, sys
import numpy as np
from mathutils import Vector, kdtree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
co0 = np.array([v.co[:] for v in bpy.data.objects['Body'].data.vertices])
bpy.ops.wm.open_mainfile(filepath=a[1])
me = bpy.data.objects['Body'].data
co1 = np.array([v.co[:] for v in me.vertices])
assert len(co0) == len(co1)
t = kdtree.KDTree(len(co0))
for i, p in enumerate(co0): t.insert(Vector(p), i)
t.balance()
seen = set(); groups = 0; gap = 0.0
for i, p in enumerate(co0):
    if i in seen: continue
    g = [h[1] for h in t.find_range(Vector(p), 1e-5)]
    if len(g) > 1:
        seen.update(g); groups += 1
        gap = max(gap, float(np.ptp(co1[g], 0).max()))
        co1[g] = co1[g].mean(0)
for v in me.vertices: v.co = Vector(co1[v.index])
me.update(); bpy.ops.wm.save_as_mainfile(filepath=a[2])
np.save(a[2].replace('.blend', '_move.npy'), np.concatenate([co0, co1 - co0], 1))
print('REWELD groups', groups, 'max gap closed mm', round(gap * 1000, 2))
