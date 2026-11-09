"""Bind positions of the grafted hands' vertices (face attribute `hand` = 1) in the exported GLB's space (glTF y-up, armature lift added)
for sleeve_poke_gate.py: Kira's gloves are in the body material, so the gate cannot pick them by material. Args: <blend> <out npy> <lift>"""
import bpy, sys
import numpy as np
IN, OUT, LIFT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
me = bpy.data.objects['Body'].data
h = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', h)
vs = sorted({v for p in me.polygons if h[p.index] for v in p.vertices})
P = np.array([me.vertices[v].co[:] for v in vs])
G = np.c_[P[:, 0], P[:, 2] + float(LIFT), -P[:, 1]]
np.save(OUT, G); print('HANDPOS', len(G))
