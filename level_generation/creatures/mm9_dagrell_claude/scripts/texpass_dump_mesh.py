"""Texture pass: dump Body (rest pose) to npz (positions, triangles, loop UVs) for chart experiments. Args: <blend> <npz>"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
me = bpy.data.objects['Body'].data
pos = np.array([v.co for v in me.vertices]); tri = np.array([p.vertices[:] for p in me.polygons])
uv = np.zeros(len(me.loops)*2); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
fuv = np.array([uv[list(p.loop_indices)] for p in me.polygons])
np.savez(argv[1], positions=pos, triangles=tri, uv=fuv)
