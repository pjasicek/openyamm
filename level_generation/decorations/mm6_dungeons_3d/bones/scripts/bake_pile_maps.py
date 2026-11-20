"""Bake the skull pile's ambient occlusion and object-space normals into its UV layout (Cycles, 2048), for the native
shading transfer (shade_pile.py): work/skullpile_ao.png, work/skullpile_nrm.png.
Usage: blender --background ../work/skullpile_tex.blend --python bake_pile_maps.py"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

SIZE = 2048
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.world = scene.world or bpy.data.worlds.new('World')
scene.world.light_settings.distance = blib.u(40)
obj = bpy.data.objects['skullpile']
for o in bpy.data.objects:
    o.select_set(o is obj)
bpy.context.view_layer.objects.active = obj
mat = obj.data.materials[0]
nodes = mat.node_tree.nodes
target = nodes.new('ShaderNodeTexImage')
nodes.active = target
for kind in ('AO', 'NORMAL'):
    image = bpy.data.images.new(f'bake_{kind}', SIZE, SIZE, float_buffer=False)
    image.colorspace_settings.name = 'Non-Color'
    target.image = image
    settings = scene.render.bake
    settings.margin = 8
    if kind == 'NORMAL':
        settings.normal_space = 'OBJECT'
        bpy.ops.object.bake(type='NORMAL', margin=8)
    else:
        bpy.ops.object.bake(type='AO', margin=8)
    path = os.path.join(blib.WORK, f"skullpile_{'ao' if kind == 'AO' else 'nrm'}.png")
    image.filepath_raw = path; image.file_format = 'PNG'; image.save()
    print('BAKED', kind, path)
