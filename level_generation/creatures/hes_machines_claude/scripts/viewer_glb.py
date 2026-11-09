"""Viewer copy (review only, not a runtime file): the runtime export as the game gets it (LOD0, rig, clips, emission),
the turret with its mount decoration added at the shared origin; a machine without an Attack clip gets one (0.5 s of
its Standing pose: its binding plays Standing for attacks), because the viewer has one clip list for all models.
The viewer has one clip list for all models, so every Attack is padded to the emplacement's 1.0 s.
Args: -- <runtime glb> <out glb> [mount glb]"""
import os
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
runtime, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30                       # before the import: it keys the clips at the scene rate
bpy.ops.import_scene.gltf(filepath=os.path.abspath(runtime))
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        bpy.data.objects.remove(o)
if len(args) > 2:
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(args[2]))
if 'Attack' not in bpy.data.actions:
    attack = bpy.data.actions['Standing'].copy(); attack.name = 'Attack'; attack.use_fake_user = True
    attack.use_frame_range = True
    attack.frame_start, attack.frame_end = 0, 15
# the viewer has one clip list: Attack is 1.0 s (the emplacement's wind-up); shorter attacks hold their last frame
attack = bpy.data.actions['Attack']
attack.use_frame_range = True
attack.frame_start, attack.frame_end = 0, max(30, int(attack.frame_range[1]))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', export_animations=True,
                          export_animation_mode='ACTIONS', export_yup=True, export_force_sampling=True)
print('VIEWERGLB', out)
