"""Render the source Wyrm and the retopology REA_TAG side by side in clip poses (textured and wireframe)
-> review/<tag>/<pose>_<view>_{source,retopo,wire}.png"""
import math
import os
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = os.environ['REA_TAG']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'retopo_{TAG}.blend'))
scene = bpy.context.scene
rig = bpy.data.objects['Wyrm_Rig']
src = bpy.data.objects['Wyrm']
new = bpy.data.objects[f'Wyrm_{TAG}']
for o in bpy.data.objects:
    if o.type == 'MESH' and o not in (src, new):
        o.hide_render = True
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.32, 0.33, 0.36, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); scene.collection.objects.link(sun)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50
scene.render.resolution_x, scene.render.resolution_y = 700, 500
out = os.path.join(HERE, 'review', TAG); os.makedirs(out, exist_ok=True)
# model space: about 1 m long along Y (head toward -Y), 0.43 m tall
views = {'three_quarter': ((1.1, -1.25, 0.45), (0, -0.05, 0.18)), 'side': ((1.6, 0.0, 0.25), (0, 0.0, 0.18)),
         'head': ((0.45, -0.95, 0.35), (0, -0.42, 0.25)),
         # close views of the areas reviewed by the user: face and throat, back spines, front feet
         'face_front': ((0.0, -0.95, 0.30), (0, -0.40, 0.27)), 'spines': ((0.35, 0.05, 0.42), (0, 0.05, 0.25)),
         'paws_front': ((0.08, -0.55, 0.10), (0, -0.20, 0.02)),
         'face_close': ((0.0, -0.66, 0.30), (0, -0.40, 0.26)), 'paws_close': ((0.0, -0.42, 0.07), (0, -0.25, 0.02))}
poses = [('Standing', 1), ('Attack', 13), ('Walking', 6)]
if os.environ.get('REA_VIEWS'):
    views = {k: v for k, v in views.items() if k in os.environ['REA_VIEWS'].split(',')}
    poses = poses[:1]
wire = bpy.data.materials.new('Wire'); wire.use_nodes = True
for action, frame in poses:
    rig.animation_data.action = bpy.data.actions[action]
    scene.frame_set(frame)
    for vname, (loc, tgt) in views.items():
        cam.location = Vector(loc)
        cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        for label, obj in (('source', src), ('retopo', new)):
            src.hide_render = obj is not src
            new.hide_render = obj is not new
            scene.render.filepath = os.path.join(out, f'{action}_{vname}_{label}.png')
            bpy.ops.render.render(write_still=True)
        # wireframe of the retopology (workbench)
        if action == 'Standing':
            src.hide_render = True; new.hide_render = False
            scene.render.engine = 'BLENDER_WORKBENCH'
            scene.display.shading.show_object_outline = False
            scene.display.shading.light = 'STUDIO'
            scene.display.shading.color_type = 'SINGLE'
            wf = new.modifiers.new('WF', 'WIREFRAME'); wf.thickness = 0.0012; wf.use_replace = False
            scene.render.filepath = os.path.join(out, f'{action}_{vname}_wire.png')
            bpy.ops.render.render(write_still=True)
            new.modifiers.remove(wf)
            src.hide_render = False; new.hide_render = True
            wf = src.modifiers.new('WF', 'WIREFRAME'); wf.thickness = 0.0012; wf.use_replace = False
            scene.render.filepath = os.path.join(out, f'{action}_{vname}_wire_source.png')
            bpy.ops.render.render(write_still=True)
            src.modifiers.remove(wf)
            scene.render.engine = 'BLENDER_EEVEE'
print('RENDERED', out)
