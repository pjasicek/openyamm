"""Diagnosis: a GLB clip pose (Blender import), the right hand framed, MM9's handle axis drawn as a thin rod on Xhammer's +Y (glTF) axis.
Args: <glb> <clip> <frame> <out prefix> [rod radius] [ortho] [bone to frame]"""
import bpy, sys, math
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
act = bpy.data.actions[a[1]]
rig.animation_data_create(); rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
bpy.context.scene.frame_set(int(a[2])); bpy.context.view_layer.update()
rad = float(a[4]) if len(a) > 4 else 0.032
if rad > 0 and 'Xhammer' in rig.pose.bones:
    pb = rig.pose.bones['Xhammer']; M = rig.matrix_world @ pb.matrix
    # glTF node +Y is the bone's own +Y in Blender's import (bone axis = node Y)
    ax = (M.to_3x3() @ Vector((0, 1, 0))).normalized(); o = M.to_translation()
    bpy.ops.mesh.primitive_cylinder_add(radius=rad, depth=3.0, location=o + ax * 0.8, rotation=ax.to_track_quat('Z', 'Y').to_euler())
fb = a[6] if len(a) > 6 else 'Bip01 R Hand'
c = (rig.matrix_world @ rig.pose.bones[fb].matrix).to_translation()
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .76, .72)
sc.render.resolution_x = sc.render.resolution_y = 600
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[5]) if len(a) > 5 else 0.5
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
for v, d in {'front': (0, -1, 0), 'side': (-1, 0, 0), 'top': (0, -0.001, 1), 'q': (-1, -1, 0.6)}.items():
    d = Vector(d).normalized(); cam.location = c + d * 5; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{a[3]}_{v}.png'; bpy.ops.render.render(write_still=True)
