"""Diagnosis: a GLB clip pose (Blender import), clay, four views framed on a bone. Args: <glb> <clip> <frame> <out prefix> [ortho] [bone] [views]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if a[1] != '-':
    act = bpy.data.actions[a[1]]
    rig.animation_data_create(); rig.animation_data.action = act
    try: rig.animation_data.action_slot = act.slots[0]
    except Exception: pass
else:
    if rig.animation_data: rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.scene.frame_set(int(a[2])); bpy.context.view_layer.update()
fb = a[5] if len(a) > 5 else 'Bip01 Pelvis'
c = (rig.matrix_world @ rig.pose.bones[fb].matrix).to_translation()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72); sh.show_cavity = True; sh.show_backface_culling = True
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.2, 0.2, 0.22)
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[4]) if len(a) > 4 else 2.6
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
V = {'q34': (-1, -1.2, 0.35), 'front': (0, -1, 0.05), 'side': (-1, 0, 0.05), 'back': (0.3, 1, 0.2), 'low': (-0.6, -1, -0.5), 'top': (0, -0.3, 1)}
names = a[6].split(',') if len(a) > 6 else ['q34', 'front', 'side', 'back']
for v in names:
    d = Vector(V[v]).normalized(); cam.location = c + d * 6; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[3]}_{v}.png'; bpy.ops.render.render(write_still=True)
