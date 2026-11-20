"""Texture pass step 4 (Blender): short-range AO on the new layout, as the production bake (reach 4 cm,
claude_shared/bake_creature_ao.py), on the welded bind-pose LOD0 with the texpass UVs.
Args: <uv_input.npz> <uv_layout.npz> <out.png> [size]
"""
import os
import runpy
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, LAYOUT, OUT = argv[:3]
SIZE = argv[3] if len(argv) > 3 else '2048'
data, layout = np.load(IN), np.load(LAYOUT)
positions, faces = data['positions'], data['faces']
bpy.ops.wm.read_factory_settings(use_empty=True)
blender_positions = np.stack([positions[:, 0], -positions[:, 2], positions[:, 1]], 1)
me = bpy.data.meshes.new('Body')
me.from_pydata(blender_positions.tolist(), [], faces.tolist())
me.update()
layer = me.uv_layers.new(name='UVMap')
corner_uv = layout['corner_uv']
for p in me.polygons:
    for k, loop in enumerate(p.loop_indices):
        layer.data[loop].uv = corner_uv[p.index, k]
for p in me.polygons:
    p.use_smooth = True
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ['bake_creature_ao.py', '--', 'Body', OUT, '0.04', SIZE]
runpy.run_path(os.path.join(here, '..', '..', 'claude_shared', 'bake_creature_ao.py'), run_name='__main__')
