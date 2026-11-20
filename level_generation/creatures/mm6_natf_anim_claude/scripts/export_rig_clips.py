"""Export the rig (with the swing helpers) and every action of a skirt_skin.py blend at 60 Hz: the source of the helper
channels for add_helpers.py. Usage: blender -b -P export_rig_clips.py -- <blend> <out.glb>"""
import os, sys, bpy
blend, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; sc.render.fps = 60; sc.render.fps_base = 1
rig = bpy.data.objects['Rig']; rig.animation_data.action = bpy.data.actions['Standing']
for o in bpy.data.objects:
    o.select_set(o.name in ('Rig', 'Body'))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_anim_slide_to_zero=False, export_image_format='NONE')
print('EXPORTED', sorted(a.name for a in bpy.data.actions))
