"""Frames of a clip at the viewer's 48 fps (frame k = k/48 s) from a review-viewer GLB, fixed three-quarter camera
-> review/attack/<label>_f<NN>.png. Usage: blender -b -P strip_frames.py -- <glb> <label> <first> <last> [clip]"""
import math, os, sys, bpy
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]; glb, label, k0, k1 = a[0], a[1], int(a[2]), int(a[3]); clip = a[4] if len(a) > 4 else 'Attack'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'attack'); os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for x in bpy.data.actions if x.name.split('|')[-1] == clip or x.name == clip)
rig.animation_data.action = act
if act.slots:
    rig.animation_data.action_slot = act.slots[0]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.4
c = Vector((0, -.2, 1.1)); d = Vector((.55, -1, .3)).normalized(); cam.location = c + d * 6
cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), 0, math.radians(-35)); sc.view_settings.view_transform = 'Standard'
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x = sc.render.resolution_y = 260
for k in range(k0, k1 + 1):
    fr = act.frame_range[0] + k / 48 * 24; sc.frame_set(int(fr), subframe=fr - int(fr))
    sc.render.filepath = os.path.join(out, f'{label}_f{k:02d}.png'); bpy.ops.render.render(write_still=True)
print('STRIP', label, k0, k1)
