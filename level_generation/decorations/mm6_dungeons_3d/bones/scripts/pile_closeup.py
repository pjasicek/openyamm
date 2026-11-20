"""Front orthographic flat (emission: base colour x COLOR_0) render of the pile LOD0 at the x2 sprite's scale, for a
side-by-side with the restored sprite. Usage: blender --background ../work/skullpile.blend --python pile_closeup.py --
<out.png> [scale] [yaw degrees] [--lit: principled material, sun and sky instead of flat emission]"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
LIT_FLAG = '--lit' in args
args = [a for a in args if a != '--lit']
out = args[0]
zoom = float(args[1]) if len(args) > 1 else 2.0
yaw = math.radians(float(args[2])) if len(args) > 2 else 0.0
U = 1 / 81.7
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
obj = bpy.data.objects['SkullPile']
for o in scene.objects:
    o.hide_render = o is not obj
LIT = LIT_FLAG
if LIT:
    world = scene.world or bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
    next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = 0.35
    sun = bpy.data.objects.new('S', bpy.data.lights.new('S', 'SUN')); scene.collection.objects.link(sun)
    sun.data.energy = 2.2; sun.rotation_euler = (math.radians(50), 0, math.radians(-25))
for m in ([] if LIT else obj.data.materials):
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image.colorspace_settings.name == 'sRGB')
    attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Color'
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    nt.links.new(tex.outputs['Color'], mix.inputs['A']); nt.links.new(attr.outputs['Color'], mix.inputs['B'])
    emit = nt.nodes.new('ShaderNodeEmission'); nt.links.new(mix.outputs['Result'], emit.inputs['Color'])
    output = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(emit.outputs['Emission'], output.inputs['Surface'])
width, height = 214, 153
scene.render.resolution_x = int(width * zoom); scene.render.resolution_y = int(height * zoom)
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'
cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = width * U
d = Vector((math.sin(yaw), -math.cos(yaw), 0))
cam.location = Vector((0, 0, height / 2 * U)) + d * 10
cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
