"""Eevee review renders of the Harvester actor (export/hes_harvester.blend, after hes_turrets_claude's
render_review_v2.py): clip frames from a few cameras, on a grey ground plane at z = 0 (so the dig shows the drill
going in). The glow material emits its emissive swatches x 2 and the hull its orange seams (textures/harvester_seam_mask.png) as a
stand-in for the engine's emissive + bloom. Writes review/poses/<clip>_<frame>_<camera>.png.
Args: -- <clip:frame:camera> [...]   cameras: 34 (front three-quarter of the left side), side (left), right,
front, back, top, vent (close-up of the left vent), nozzle (close-up of the sprayer)"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
specs = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'export', 'hes_harvester.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']
for o in list(scene.objects):
    if o.type == 'MESH' and o.name != 'Harvester':
        o.hide_render = True
mat = bpy.data.materials['HS_Glow_Harvester']            # its emissive texture is linked by build_actor.py
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Emission Strength'].default_value = 2.0
hull = bpy.data.materials['HS_Harvester']                 # the orange seams: emission = orange x the seam mask
hn, hl = hull.node_tree.nodes, hull.node_tree.links
hb = hn['Principled BSDF']
seam = hn.new('ShaderNodeTexImage')
seam.image = bpy.data.images.load(os.path.join(HERE, 'textures', 'harvester_seam_mask.png'))
seam.image.colorspace_settings.name = 'Non-Color'
gain = hn.new('ShaderNodeMath'); gain.operation = 'MULTIPLY'; gain.inputs[1].default_value = 3.0
hl.new(seam.outputs['Color'], gain.inputs[0]); hl.new(gain.outputs['Value'], hb.inputs['Emission Strength'])
hb.inputs['Emission Color'].default_value = (1.0, 0.42, 0.1, 1)
engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1000, 700
world = scene.world or bpy.data.worlds.new('World'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.16, 0.15, 0.15, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.4
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); scene.collection.objects.link(sun)
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(45), 0, math.radians(30))
fill = bpy.data.objects.new('Fill', bpy.data.lights.new('Fill', 'SUN')); scene.collection.objects.link(fill)
fill.data.energy = 1.0; fill.rotation_euler = (math.radians(70), 0, math.radians(200))
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.active_object
gm = bpy.data.materials.new('ground'); gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.2, 0.17, 1)
ground.data.materials.append(gm)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
CAMS = {'34': ((-9.0, -12.5, 4.5), (0, -0.6, 1.3), 40), 'side': ((-15.0, -0.5, 2.0), (0, -0.5, 1.4), 45),
        'right': ((15.0, -0.5, 2.0), (0, -0.5, 1.4), 45), 'front': ((0, -16, 2.5), (0, 0, 1.4), 45),
        'back': ((-6.0, 13.0, 5.0), (0, 1.0, 1.6), 40), 'top': ((0.01, -0.5, 22.0), (0, -0.5, 0), 40),
        'vent': ((-4.5, -6.5, 3.6), (1.27, -2.3, 1.95), 50), 'nozzle': ((-4.5, 7.5, 4.5), (-0.9, 3.6, 2.6), 60)}
# 'left' side of the machine is +x: the cameras sit at -x... keep the names as the actor's sides
CAMS['34'] = ((9.0, -12.5, 4.5), (0, -0.6, 1.3), 40)
CAMS['side'] = ((15.0, -0.5, 2.0), (0, -0.5, 1.4), 45)
CAMS['right'] = ((-15.0, -0.5, 2.0), (0, -0.5, 1.4), 45)
CAMS['vent'] = ((4.8, -6.8, 3.6), (1.27, -2.3, 1.95), 50)
os.makedirs(os.path.join(HERE, 'review', 'poses'), exist_ok=True)
for spec in specs:
    clip, frame, view = spec.split(':')
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(int(frame))
    loc, target, lens = CAMS[view]
    cam.data.lens = lens
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(HERE, 'review', 'poses', f'{clip}_{frame}_{view}.png')
    bpy.ops.render.render(write_still=True)
print('REVIEW done', len(specs))
