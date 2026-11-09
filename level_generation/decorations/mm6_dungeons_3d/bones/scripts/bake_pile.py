"""High-to-low bake of the skull pile (work/pile_low.blend: 'high' = full-detail Meshy pile with its texture, 'low' =
the game mesh with its UVs, plus 'far' from add_far_lod.py): base colour (diffuse colour pass), tangent-space normals and ambient occlusion of the high
mesh (distance AO_UNITS map units; the low mesh is invisible to rays) onto the low mesh's UVs at SIZE px, Cycles
selected-to-active. Writes work/pilebake_{base,normal,ao,objnormal}_<SIZE>.png (objnormal: object-space normals for the light
term of compose_pile.py).
Usage: blender --background ../work/pile_low.blend --python bake_pile.py -- [size] [passes, default base,normal,ao,objnormal]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
SIZE = int(args[0]) if args else 2048
PASSES = args[1].split(',') if len(args) > 1 else ['base', 'normal', 'ao', 'objnormal']
AO_UNITS = 30.0
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.world = scene.world or bpy.data.worlds.new('World')
scene.world.light_settings.distance = blib.u(AO_UNITS)
high = bpy.data.objects['high']
# Bake LOD0 and the far mesh (add_far_lod.py) in one go: a joined copy (their charts do not overlap in the atlas).
parts = [blib.duplicate(bpy.data.objects[n], n + '_bake') for n in ('low', 'far') if n in bpy.data.objects]
low = blib.pl.join('bake_target', parts) if len(parts) > 1 else parts[0]
for obj in bpy.data.objects:                       # only the high mesh may block rays (AO, cage)
    if obj is not high and obj.type == 'MESH':
        for attr in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission',
                     'visible_volume_scatter', 'visible_shadow'):
            setattr(obj, attr, False)
mat = bpy.data.materials.new('Bake'); mat.use_nodes = True
low.data.materials.clear(); low.data.materials.append(mat)
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); mat.node_tree.nodes.active = node
for o in bpy.data.objects:
    o.select_set(o in (high, low))
bpy.context.view_layer.objects.active = low
bake = scene.render.bake
bake.use_selected_to_active = True
bake.cage_extrusion = blib.u(4.0)
bake.max_ray_distance = blib.u(9.0)
bake.margin = 8
for name in PASSES:
    image = bpy.data.images.new(f'{name}{SIZE}', SIZE, SIZE)
    if name != 'base':
        image.colorspace_settings.name = 'Non-Color'
    node.image = image
    if name == 'base':
        scene.cycles.samples = 4
        bake.use_pass_direct = False; bake.use_pass_indirect = False; bake.use_pass_color = True
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
    elif name in ('normal', 'objnormal'):
        scene.cycles.samples = 4
        bake.normal_space = 'TANGENT' if name == 'normal' else 'OBJECT'
        bpy.ops.object.bake(type='NORMAL')
    else:
        scene.cycles.samples = 128
        bpy.ops.object.bake(type='AO')
    path = os.path.join(blib.WORK, f'pilebake_{name}_{SIZE}.png')
    image.filepath_raw = path; image.file_format = 'PNG'; image.save()
    print('BAKED', name, path)
