"""Review renders of a built model (its work/<prop>.blend, the scene the GLB is exported from): LOD0 front (sprite-like,
low elevation), three-quarter and side, and every LOD from the three-quarter view. Lit by a uniform white sky
(strength 1) plus a weak sun (0.4), so a surface shows about its base colour x COLOR_0, as the engine shows a sprite-
lit model at light one. Flipbook materials show their first frame, emissive like the engine's unlit flames. Base
colours are multiplied by the 'Color' attribute (COLOR_0), metallic and specular are off (dungeons have no sky to
reflect), as in the engine. Then sheet.py combines them with the native sprite.
Usage: blender --background work/<prop>.blend --python review.py -- <prop> [yaw_deg [front elevation_deg]]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hanging_lib as hl  # noqa: E402

pl = hl.pl
args = sys.argv[sys.argv.index('--') + 1:]
prop = args[0]
yaw = int(args[1]) if len(args) > 1 else 0
elevation = int(args[2]) if len(args) > 2 else 6        # the chandelier sprite is seen from below
out = os.path.join(hl.HERE, 'review', prop); os.makedirs(out, exist_ok=True)
objects = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    for key in ('Metallic', 'Roughness'):
        for link in list(bsdf.inputs[key].links):
            nt.links.remove(link)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Specular IOR Level'].default_value = 0.0     # the white sky's reflection would lift dark iron
    base = bsdf.inputs['Base Color'].links[0].from_socket
    attribute = nt.nodes.new('ShaderNodeVertexColor'); attribute.layer_name = 'Color'
    multiply = nt.nodes.new('ShaderNodeMix'); multiply.data_type = 'RGBA'; multiply.blend_type = 'MULTIPLY'
    multiply.inputs['Factor'].default_value = 1.0
    colour_in = [socket for socket in multiply.inputs if socket.type == 'RGBA']
    colour_out = next(socket for socket in multiply.outputs if socket.type == 'RGBA')
    nt.links.new(base, colour_in[0]); nt.links.new(attribute.outputs['Color'], colour_in[1])
    nt.links.new(colour_out, bsdf.inputs['Base Color'])
for m in bpy.data.materials:
    flip = m.get('openyamm_flipbook')
    if flip is not None and m.node_tree:
        nt = m.node_tree
        tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        coord = nt.nodes.new('ShaderNodeTexCoord'); mapping = nt.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1 / flip[0], 1 / flip[1], 1)
        mapping.inputs['Location'].default_value = (0, 1 - 1 / flip[1], 0)
        nt.links.new(coord.outputs['UV'], mapping.inputs['Vector'])
        nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
scene = pl.setup_render((512, 768))
bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0); bg.inputs['Strength'].default_value = 1.0
bpy.data.lights['Sun'].energy = 0.4
lod0 = min(objects, key=lambda o: len(o.name))
pl.render_views([lod0], out, 'lod0', views=((yaw, elevation), (yaw + 40, 22), (yaw + 90, elevation + 2)))
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'level{level}', views=((yaw + 40, 22),))
print('REVIEW', out, [o.name for o in objects])
