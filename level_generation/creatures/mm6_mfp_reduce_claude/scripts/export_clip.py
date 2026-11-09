"""Export one action of the authoring blend as a GLB with only the armature and that clip (sampled every frame, all
channels, no optimisation) for splice_clip.py. Args: -- <blend> <action> <out glb>"""
import bpy, sys, os
blend, an, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; sc.render.fps = 30; sc.render.fps_base = 1
rig = bpy.data.objects['Rig']
for a in list(bpy.data.actions):
    if a.name != an: bpy.data.actions.remove(a)
act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
for o in bpy.data.objects: o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', use_selection=True, export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_optimize_animation_size=False, export_optimize_animation_keep_anim_armature=True,
                          export_frame_range=False, export_skins=False, export_def_bones=False)
print('EXPORTED', an, out)
