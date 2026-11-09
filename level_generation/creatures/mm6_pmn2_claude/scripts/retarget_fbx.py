"""Retarget a Mixamo FBX animation (mixamorig:* bones, T-pose rest, cm) onto the pmn2 Meshy rig (same bone names,
A-pose rest). Args: in_blend fbx action_name out_blend.
Per bone, the target's rest frame is first swung so its bone direction matches the source rest direction; the fixed
offset O = S_rest^-1 @ that aligned frame then gives T(f) = S(f) @ O, so every bone points where the source bone
points and keeps the source twist (hands keep the source's grip orientation). Hips translation is scaled by the
hips-height ratio. Fingers and bones missing on either side are skipped. Keys are one per source frame; the scene is
put back to 24 fps (the FBX import sets the source rate, which would rescale every other clip on export)."""
import bpy, sys, os
from mathutils import Matrix, Vector
args = sys.argv[sys.argv.index('--') + 1:]
in_blend, fbx, name, out_blend = args
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(in_blend))
tgt = bpy.data.objects['Mage_Rig']
before = set(bpy.data.objects); acts_before = set(bpy.data.actions)
bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
FPS = bpy.context.scene.render.fps                         # the FBX import switches the scene to its own rate
src = next(o for o in set(bpy.data.objects) - before if o.type == 'ARMATURE')
src_act = next(iter(set(bpy.data.actions) - acts_before))
src.animation_data.action = src_act
SKIP = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Eye', 'Jaw', 'Armour', 'End')
names = [b.name for b in tgt.data.bones if b.name in src.data.bones and not any(k in b.name for k in SKIP)]
SW, TW = src.matrix_world, tgt.matrix_world
Y = Vector((0, 1, 0))
offset = {}
for n in names:
    Rs = (SW @ src.data.bones[n].matrix_local).to_3x3().normalized()
    Rt = (TW @ tgt.data.bones[n].matrix_local).to_3x3().normalized()
    swing = (Rt @ Y).rotation_difference(Rs @ Y).to_matrix()
    offset[n] = Rs.inverted() @ (swing @ Rt)
hs = (SW @ src.data.bones['mixamorig:Hips'].head_local).z
ht = (TW @ tgt.data.bones['mixamorig:Hips'].head_local).z
k = ht / hs
src_hips0 = None
act = bpy.data.actions.new(name); act.use_fake_user = True
tgt.animation_data_create(); tgt.animation_data.action = act
f0, f1 = (int(round(x)) for x in src_act.frame_range)
scene = bpy.context.scene
for i, f in enumerate(range(f0, f1 + 1)):
    scene.frame_set(f)
    for n in names:                                          # parents first (bone order)
        pb = tgt.pose.bones[n]; spb = src.pose.bones[n]
        Sw = (SW @ spb.matrix)
        R = Sw.to_3x3().normalized() @ offset[n]
        M = R.to_4x4()
        if n == 'mixamorig:Hips':
            p = Sw.translation
            if src_hips0 is None:
                src_hips0 = p.copy()
            th = TW @ tgt.data.bones[n].head_local
            M.translation = Vector((th.x + (p.x - src_hips0.x) * k, th.y + (p.y - src_hips0.y) * k, p.z * k))
        else:
            M.translation = TW @ pb.head
        pb.rotation_mode = 'QUATERNION'
        pb.matrix = TW.inverted() @ M
        bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion', frame=i)
        if n == 'mixamorig:Hips':
            pb.keyframe_insert('location', frame=i)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, f1 - f0
bpy.data.objects.remove(src, do_unlink=True)
for o in list(set(bpy.data.objects) - before):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.data.actions.remove(src_act)
bpy.context.scene.render.fps = 24                         # rig clips are authored at 24 fps; keys are one per source frame
print('RETARGET', name, 'source fps', FPS, 'frames', f1 - f0 + 1, 'bones', len(names), 'hips scale', round(k, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
