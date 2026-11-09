"""Export the natf master with candidate clips for the review viewer: body, blade and shield, every listed action
(renamed for display), textures embedded. Action=Name@0.5 scales its key times (the accepted clips are keyed at 60 Hz,
the retargets at the scene's 30). Usage: blender -b -P export_candidates.py -- <blend> <out.glb> <Action=Name[@scale]> [...]"""
import os, sys, bpy
a = sys.argv[sys.argv.index('--') + 1:]
blend, out = a[0], a[1]
pairs = [p.split('=') for p in a[2:]]
scale = {act: float(name.split('@')[1]) for act, name in pairs if '@' in name}
pairs = [(act, name.split('@')[0]) for act, name in pairs]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
keep = {act: name for act, name in pairs}
for act in list(bpy.data.actions):
    if act.name not in keep:
        bpy.data.actions.remove(act)
for act in list(bpy.data.actions):  # snapshot: renaming reorders the collection
    if act.name in scale:
        k = scale[act.name]
        for fc in act.fcurves if hasattr(act, 'fcurves') else [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]:
            for kp in fc.keyframe_points:
                kp.co.x *= k; kp.handle_left.x *= k; kp.handle_right.x *= k
        act.frame_range = (act.frame_range[0] * k, act.frame_range[1] * k)
    act.name = keep[act.name]; act.use_fake_user = True
rig = bpy.data.objects['Rig']
rig.animation_data.action = bpy.data.actions[pairs[0][1]]
for o in bpy.data.objects:
    o.select_set(o.name in ('Rig', 'Body', 'ForearmBlade', 'LeafShield'))
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_anim_slide_to_zero=True)
print('EXPORTED', out, [x.name for x in bpy.data.actions])
