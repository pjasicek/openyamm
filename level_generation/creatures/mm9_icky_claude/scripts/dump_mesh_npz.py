"""Dump a blend object's vertices (world) and faces to npz. Args: blend object out.npz"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects[argv[1]]
V = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
F = np.array([tuple(p.vertices) for p in o.data.polygons if len(p.vertices) == 3])
np.savez(argv[2], V=V, F=F)
print('DUMP', V.shape, F.shape)
