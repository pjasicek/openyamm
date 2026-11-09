"""Dump 'Body' bind positions, normals, triangles, piece, weights (dense) to npz. Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Body']; me = o.data
names = [g.name for g in o.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
np.savez(argv[1], P=np.array([tuple(v.co) for v in me.vertices]), N=np.array([tuple(v.normal) for v in me.vertices]),
         T=np.array([tuple(p.vertices) for p in me.polygons]), piece=np.array([d.value for d in me.attributes['piece'].data]),
         W=W, names=np.array(names))
print('DUMP', len(me.vertices), len(me.polygons))
