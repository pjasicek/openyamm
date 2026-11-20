"""Export a centaur master .blend (body, rig, sockets, all actions) to a LOD0 GLB with the settings of export_model.py.
Usage: blender -b -P export_master_lod0.py -- <master.blend> <out.glb>"""
import bpy, sys
blend, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']
rig.animation_data.action = bpy.data.actions['Standing']; rig.animation_data.action_slot = rig.animation_data.action.slots[0]; sc.frame_set(0)
for o in sc.objects:
    o.select_set(o == b or o == rig or o.name.startswith('Socket_'))
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_force_sampling=True, export_frame_step=1, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False, export_image_format='AUTO',
                          export_reset_pose_bones=True, export_anim_slide_to_zero=True, export_extras=True)
print('EXPORTED', out)
