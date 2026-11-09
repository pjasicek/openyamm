"""Pieces with vertices weighted to a bone (weight > 0.3): piece id, garment label, count, rest bounds. Args: -- <blend> <bone>"""
import bpy, sys, os
import numpy as np
blend, bone = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
gi = body.vertex_groups[bone].index
co = np.array([tuple(v.co) for v in me.vertices])
w = np.array([sum(e.weight for e in v.groups if e.group == gi) for v in me.vertices])
for p in sorted(set(pv[w > 0.3].tolist())):
    m = (pv == p) & (w > 0.3)
    print('FOLLOWS', bone, 'piece', p, 'garment', int(gv[m][0]), 'verts', int(m.sum()), 'of', int((pv == p).sum()),
          'lo', np.round(co[pv == p].min(0), 3).tolist(), 'hi', np.round(co[pv == p].max(0), 3).tolist())
