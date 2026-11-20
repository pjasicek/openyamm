"""Behemoth part labels as the point attribute 'garment' (used by uv_raster.py and the compose): 0 skin (piece 0),
1 mane shingles (other pieces), 9 the small pieces rigid on B_Head (teeth, tusks, eyes). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
hg = {body.vertex_groups[n].index for n in ('B_Head',)}
hw = np.array([sum(e.weight for e in v.groups if e.group in hg) for v in me.vertices])
co = np.array([tuple(v.co) for v in me.vertices])
g = np.where(pv == 0, 0, 1).astype(np.int32)
for p in np.unique(pv[pv != 0]):
    m = pv == p
    size = (co[m].max(0) - co[m].min(0)).max()
    if (hw[m] > 0.99).all() and size < 0.2:
        g[m] = 9
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', g)
print('GARMENT verts skin', int((g == 0).sum()), 'mane', int((g == 1).sum()), 'head pieces', int((g == 9).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
