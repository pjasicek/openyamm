"""Attack clip frames at 8 evenly spaced times (front and side, matching native views 0 and 2) from a GLB with the
sword merged (mm8_m656_claude/export/mm8_m656_prepared.glb; same clip as installed) -> review/attack_native/<view>_<i>.png.
Usage: blender -b -P attack_frames.py -- <glb>"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'attack_native'); os.makedirs(out, exist_ok=True)
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions['Attack']; rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.4; sc.render.resolution_x = sc.render.resolution_y = 360
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.11, .11, .13, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
f0, f1 = act.frame_range
for i in range(8):
    fr = f0 + (f1 - f0) * i / 7.5; sc.frame_set(int(fr), subframe=fr - int(fr))
    for view, d in (('front', (0, -1, 0)), ('side', (-1, 0, 0))):
        c = Vector((0, 0, 1.0)); cam.location = c + Vector(d) * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = os.path.join(out, f'{view}_{i}.png'); bpy.ops.render.render(write_still=True)
print('ATTACKFRAMES', f0, f1)
