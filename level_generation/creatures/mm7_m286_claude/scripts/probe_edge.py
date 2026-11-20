"""Print rest data of the given vertices of 'Body' (position, piece, garment, weights) and their shared edges, and the
distance between them. Args: -- <blend> v1 v2 [...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
ob = bpy.data.objects['Body']; me = ob.data
ids = [int(x) for x in a[1:]]
names = [g.name for g in ob.vertex_groups]
for i in ids:
    v = me.vertices[i]
    w = sorted(((e.weight, names[e.group]) for e in v.groups), reverse=True)[:3]
    nb = [e.vertices[1] if e.vertices[0] == i else e.vertices[0] for e in me.edges if i in e.vertices]
    print('PROBE', i, [round(x, 4) for x in v.co], 'piece', me.attributes['piece'].data[i].value,
          'garment', me.attributes['garment'].data[i].value if 'garment' in me.attributes else None,
          [(round(x, 2), n) for x, n in w], 'neighbours', nb)
for k in range(len(ids) - 1):
    print('PROBE dist', ids[k], ids[k + 1], round((me.vertices[ids[k]].co - me.vertices[ids[k + 1]].co).length * 100, 3), 'cm')
