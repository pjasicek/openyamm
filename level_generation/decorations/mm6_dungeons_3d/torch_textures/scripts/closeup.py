"""Close-up review renders of one exported GLB's LOD0: an orthographic window over native heights z0..z1 (map units)
from the front, three-quarter and side, with the review lighting (weak key light, flipbook first frame), written as
review/<prop>/closeup_y<yaw>.png. Usage: blender --background --python closeup.py -- <prop> <export.glb> <z0> <z1>"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ttex  # noqa: E402

pl = ttex.pl
u = ttex.u
prop, glb, z0, z1 = sys.argv[sys.argv.index('--') + 1:][:4]
z0, z1 = u(float(z0)), u(float(z1))
out = os.path.join(ttex.HERE, 'review', prop); os.makedirs(out, exist_ok=True)
pl.reset()
bpy.ops.import_scene.gltf(filepath=glb)
objects = [o for o in bpy.data.objects if o.type == 'MESH']
lod0 = min(objects, key=lambda o: len(o.name))
for o in objects:
    o.hide_render = o is not lod0
for m in bpy.data.materials:
    flip = m.get('openyamm_flipbook') if m.node_tree else None
    if flip is not None:
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
scene = pl.setup_render((512, 512))
bpy.data.objects['Sun'].data.energy = 2.4
next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND').inputs['Strength'].default_value = 0.35
camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(camera); scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = (z1 - z0)
centre = Vector((0, 0, (z0 + z1) / 2))
for yaw in (0, 40, 90):
    y = math.radians(yaw); e = math.radians(6)
    d = Vector((math.sin(y) * math.cos(e), -math.cos(y) * math.cos(e), math.sin(e)))
    camera.location = centre + d * 3.0
    camera.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(out, f'closeup_y{yaw:03d}.png')
    bpy.ops.render.render(write_still=True)
print('CLOSEUP', out)
