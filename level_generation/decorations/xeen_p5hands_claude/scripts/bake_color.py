"""Re-bake only the colour and roughness on work/low.blend (its UVs kept), with lowbake.py's current stone shader.
Usage: blender -b --python bake_color.py"""
import os, sys
import bpy
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
work = os.path.join(PROJECT, 'work')
src = open(os.path.join(HERE, 'lowbake.py')).read()
a = src.index('def stone_material(name, roughness):'); b = src.index('# 2./3. Colour and roughness are evaluated')
STONE_TEX = os.path.join(REPO, 'assets_source', 'worlds', 'mm7', 'textures_x4', '7tws1h.png')
VEIN_TEX = os.path.join(REPO, 'assets_source', 'worlds', 'mm9', 'textures_x4', 'marb94orui.png')
bpy.ops.wm.open_mainfile(filepath=os.path.join(work, 'low.blend'))
exec(src[a:b])
scene = bpy.context.scene
low = bpy.data.objects['LOD0']; me = low.data
for o in scene.objects:
    o.hide_render = o is not low
    o.select_set(o is low)
bpy.context.view_layer.objects.active = low
scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 32
scene.render.bake.use_selected_to_active = False; scene.render.bake.margin = 16
keep = me.materials[0]
for name, size, rough, path in (('bake_color', 2048, False, 'bake_color.png'), ('bake_rough', 1024, True, 'bake_rough.png')):
    img = bpy.data.images.new(name + '_v2', size, size, alpha=False)
    if rough:
        img.colorspace_settings.name = 'Non-Color'
    sm = stone_material('BakeRough' if rough else 'BakeStone', rough)
    node = sm.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img
    sm.node_tree.nodes.active = node
    me.materials[0] = sm
    bpy.ops.object.bake(type='EMIT')
    img.filepath_raw = os.path.join(work, path); img.file_format = 'PNG'; img.save()
    print('BAKED', path)
me.materials[0] = keep
print('COLOR_DONE')
