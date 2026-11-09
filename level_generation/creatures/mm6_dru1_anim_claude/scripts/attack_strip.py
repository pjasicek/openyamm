"""Textured frame strip of one clip from a viewer GLB: every STEP-th frame in front / q34 / side, EEVEE, one row per
view -> work/strip_<view>_<frame>.png (compose with scripts/strip_sheet.py). Args: -- <glb> <clip> <label> [step]"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, clip, label = sys.argv[sys.argv.index('--') + 1:][:3]
step = int(sys.argv[sys.argv.index('--') + 4]) if len(sys.argv) > sys.argv.index('--') + 4 else 2
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[clip]; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = 300; sc.render.resolution_y = 420
sc.render.engine = 'BLENDER_EEVEE'
f0, f1 = (int(x) for x in act.frame_range)
frames = list(range(f0, f1 + 1, step)) + ([f1] if (f1 - f0) % step else [])
views = {'front': (0, -1, .1), 'q34': (.7, -.7, .2), 'side': (1, 0, .1)}
c = Vector((0, -0.15, 0.95))
for j, (v, d) in enumerate(views.items()):
    dv = Vector(d).normalized(); cam.location = c + dv * 4
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for i, f in enumerate(frames):
        sc.frame_set(f); p = os.path.join(HERE, 'work', f'strip_{v}_{f}.png'); sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
print('STRIP', ' '.join(map(str, frames)))
