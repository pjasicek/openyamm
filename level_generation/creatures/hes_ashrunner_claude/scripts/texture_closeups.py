"""Texture close-ups of a viewer GLB (review/viewer/<out>_<tier>.glb: tier colours baked), for before/after checks of
the body texture (2026-10-22 packed-UV round). EEVEE, orthographic, soft sun + sky light; frame 0 of CLIP (P_Standing in
the old GLBs, Standing in the per-tier ones). Shots: name, target (x, y, z in metres, Blender axes), view direction,
ortho size. Writes <out>_<shot>.png. Args: -- <glb> <clip>[,<clip>...] <out prefix>"""
import bpy, sys, os, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, clips, out = os.path.abspath(a[0]), a[1].split(','), os.path.abspath(a[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = next(x for c in clips for x in bpy.data.actions if x.name.split('|')[-1] == c or x.name == c)
arm.animation_data_create(); arm.animation_data.action = act
if len(act.slots):
    arm.animation_data.action_slot = act.slots[0]
sc.frame_set(0)
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng; break
    except TypeError:
        pass
sc.world = bpy.data.worlds.new('w'); sc.world.use_nodes = True
bg = sc.world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.55, 0.57, 0.6, 1); bg.inputs[1].default_value = 0.9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 2.5; sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
sc.render.resolution_x = sc.render.resolution_y = 640
sc.view_settings.view_transform = 'Standard'
# the model faces -Y in Blender after the glTF import (front camera on -Y)
SHOTS = [('body_front', (0, 0, 0.95), (0, -1, 0.05), 2.0), ('body_back', (0, 0, 0.95), (0, 1, 0.05), 2.0),
         ('cloak_back', (0, 0.1, 1.15), (0.25, 1, 0.1), 0.7), ('scarf_chest', (0, -0.1, 1.38), (0, -1, 0.05), 0.5),
         ('shoulder_l', (0.24, 0, 1.38), (0.6, -1, 0.2), 0.42), ('boots', (0, -0.05, 0.25), (0.3, -1, 0.15), 0.6),
         ('pack', (0, 0.25, 1.3), (-0.5, 1, 0.2), 0.7), ('hem', (0, 0, 0.45), (-0.8, -0.6, 0.1), 0.8)]
for name, tgt, d, size in SHOTS:
    d = Vector(d).normalized(); t = Vector(tgt)
    cam.location = t + d * 4.0
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = size
    sc.render.filepath = f'{out}_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('SHOT', sc.render.filepath)
