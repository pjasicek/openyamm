"""Export named actions of the master rig (60 Hz keys) as a clips-only GLB for merge_clips.py.
Usage: blender -b -P export_clips.py -- <blend> <out.glb> <action> [...]"""
import os, sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, names = a[1], a[2:]
sc = bpy.context.scene; sc.render.fps = 60; sc.render.fps_base = 1
for act in list(bpy.data.actions):
    if act.name not in names:
        bpy.data.actions.remove(act)
rig = bpy.data.objects['Rig']; rig.animation_data.action = bpy.data.actions[names[0]]
for o in bpy.data.objects:
    o.select_set(o.name in ('Rig', 'Body'))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_anim_slide_to_zero=True, export_image_format='NONE')
print('EXPORTED', [x.name for x in bpy.data.actions])
