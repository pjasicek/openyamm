"""Review renders of a metal prop (work/<prop>.blend) in two lights, into review/<prop>/:
- `dungeon_*`: as the engine shows an indoor decoration (fs_model.sc with IndoorRenderer's decoration lighting):
  diffuse only, base colour x (1 - metallic) x COLOR_0, under a uniform white sky and a weak sun (review.py's dungeon
  light); the faint 0.1 reflection is left out;
- `lit_*`: the authored PBR material (metallic, roughness and normal maps, base x COLOR_0) under the props library's
  sky and sun, as outdoors or under the creatures' full lighting, to show the metal itself.
LOD0 front, three-quarter and side per light, and every LOD in the lit three-quarter view (`lit_level<k>`).
Usage: blender --background work/<prop>.blend --python small_review_metal.py -- <prop> [yaw [elevation]] [--lit-only]"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

pl = dlib.pl
args = [a for a in sys.argv[sys.argv.index('--') + 1:] if not a.startswith('--')]
prop = args[0]
yaw = int(args[1]) if len(args) > 1 else 0
elevation = int(args[2]) if len(args) > 2 else 6
lit_only = '--lit-only' in sys.argv
out = os.path.join(dlib.REVIEW, prop); os.makedirs(out, exist_ok=True)
objects = sorted([o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render], key=lambda o: o.name)
lod0 = min(objects, key=lambda o: len(o.name))
setups = {}
for m in bpy.data.materials:
    if not m.node_tree:
        continue
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None or not bsdf.inputs['Base Color'].links:
        continue
    base = bsdf.inputs['Base Color'].links[0].from_socket
    attribute = nt.nodes.new('ShaderNodeVertexColor'); attribute.layer_name = 'Color'
    tinted = nt.nodes.new('ShaderNodeMix'); tinted.data_type = 'RGBA'; tinted.blend_type = 'MULTIPLY'
    tinted.inputs['Factor'].default_value = 1.0
    cin = [s for s in tinted.inputs if s.type == 'RGBA']
    nt.links.new(base, cin[0]); nt.links.new(attribute.outputs['Color'], cin[1])
    tinted_out = next(s for s in tinted.outputs if s.type == 'RGBA')
    metal_socket = bsdf.inputs['Metallic'].links[0].from_socket if bsdf.inputs['Metallic'].links else None
    rough_socket = bsdf.inputs['Roughness'].links[0].from_socket if bsdf.inputs['Roughness'].links else None
    # dungeon: base x COLOR_0 x (1 - metallic), diffuse only
    diffuse = nt.nodes.new('ShaderNodeMix'); diffuse.data_type = 'RGBA'; diffuse.blend_type = 'MULTIPLY'
    diffuse.inputs['Factor'].default_value = 1.0
    din = [s for s in diffuse.inputs if s.type == 'RGBA']
    nt.links.new(tinted_out, din[0])
    if metal_socket is not None:
        invert = nt.nodes.new('ShaderNodeMath'); invert.operation = 'SUBTRACT'; invert.inputs[0].default_value = 1.0
        nt.links.new(metal_socket, invert.inputs[1])
        nt.links.new(invert.outputs[0], din[1])
    else:
        din[1].default_value = (1, 1, 1, 1)
    setups[m.name] = (nt, bsdf, tinted_out, next(s for s in diffuse.outputs if s.type == 'RGBA'), metal_socket,
                      rough_socket)


def mode(name):
    for nt, bsdf, tinted_out, diffuse_out, metal_socket, rough_socket in setups.values():
        for key in ('Base Color', 'Metallic', 'Roughness'):
            for link in list(bsdf.inputs[key].links):
                nt.links.remove(link)
        if name == 'dungeon':
            nt.links.new(diffuse_out, bsdf.inputs['Base Color'])
            bsdf.inputs['Metallic'].default_value = 0.0
            bsdf.inputs['Roughness'].default_value = 0.85
            bsdf.inputs['Specular IOR Level'].default_value = 0.0
        else:
            nt.links.new(tinted_out, bsdf.inputs['Base Color'])
            if metal_socket is not None:
                nt.links.new(metal_socket, bsdf.inputs['Metallic'])
            if rough_socket is not None:
                nt.links.new(rough_socket, bsdf.inputs['Roughness'])
            bsdf.inputs['Specular IOR Level'].default_value = 0.5


scene = pl.setup_render((512, 768))
bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
views = ((yaw, elevation), (yaw + 40, 22), (yaw + 90, elevation + 2))
if not lit_only:
    mode('dungeon')
    bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0); bg.inputs['Strength'].default_value = 1.0
    bpy.data.lights['Sun'].energy = 0.4
    pl.render_views([lod0], out, 'dungeon', views=views)
mode('lit')
bg.inputs['Color'].default_value = (0.55, 0.62, 0.72, 1.0); bg.inputs['Strength'].default_value = 0.9
bpy.data.lights['Sun'].energy = 3.2
pl.render_views([lod0], out, 'lit', views=views)
for obj in objects:
    level = '0' if obj is lod0 else obj.name.rsplit('LOD', 1)[1]
    pl.render_views([obj], out, f'litlevel{level}', views=((yaw + 40, 22),))
print('REVIEW', out)
