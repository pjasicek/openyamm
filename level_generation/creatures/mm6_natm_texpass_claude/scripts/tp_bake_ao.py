"""Short-range AO of the installed LOD0 (every atlas primitive) on a texture-pass layout (Blender, Cycles CPU), as
claude_shared/bake_creature_ao.py but on the welded LOD0 surface rebuilt from work/lod0_before.npz with the layout's
UVs (bind pose: the GLB's rest positions).
Args: <layout npz> <out png> [reach m 0.035] [size 2048]"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
layout = np.load(args[0])
out = args[1]
reach = float(args[2]) if len(args) > 2 else 0.035
size = int(args[3]) if len(args) > 3 else 2048
d = np.load(os.path.join(HERE, 'work', 'lod0_before.npz'))
pos, tri, weld = d['pos'], d['tri'], d['weld']
nweld = int(weld.max()) + 1
wpos = np.zeros((nweld, 3))
wpos[weld] = pos
blender = np.stack([wpos[:, 0], -wpos[:, 2], wpos[:, 1]], 1)
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body')
me.from_pydata(blender.tolist(), [], weld[tri].tolist())
me.update()
for p in me.polygons:
    p.use_smooth = True
layer = me.uv_layers.new(name='UVMap')
uv = layout['uv'].copy()
uv[..., 1] = 1 - uv[..., 1]
loops = np.zeros((len(me.loops), 2), np.float32)
for p in me.polygons:
    loops[list(p.loop_indices)] = uv[p.index]
layer.data.foreach_set('uv', loops.ravel())
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 96
sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = reach
img = bpy.data.images.new('ao', size, size, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake')
mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage')
node.image = img
mat.node_tree.nodes.active = node
me.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
img.filepath_raw = out
img.file_format = 'PNG'
img.save()
print('BAKED', out)
