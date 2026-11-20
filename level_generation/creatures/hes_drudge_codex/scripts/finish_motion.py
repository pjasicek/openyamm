"""Local corrections to the Drudge's bound motions; retains all shared source actions separately."""
import bpy,math,os,sys,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/run_fitted.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['HKR']
scene.render.fps=30
bpy.context.preferences.filepaths.save_version=0
bpy.context.preferences.filepaths.use_file_compression=True

def action(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snapshot(): return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def apply(pose):
    action(None)
    for b in rig.pose.bones:b.matrix_basis=pose[b.name]
    bpy.context.view_layer.update()
action(bpy.data.actions['Demon_Standing']);scene.frame_set(0)
open_fingers={b.name:b.matrix_basis.copy() for b in rig.pose.bones if 'Finger' in b.name}
records={};new_actions=[]
for source,name,spread in [('Demon_Walking','Drudge_Walking',14),('Drudge_Running','Drudge_Running',0),('Carbine_Death','Drudge_Death',12)]:
    old=bpy.data.actions[source];n=int(round(old.frame_range[1]));poses=[];lifts=[]
    for f in range(n+1):
        action(old);scene.frame_set(f);snap=snapshot();apply(snap)
        for bone,m in open_fingers.items():rig.pose.bones[bone].matrix_basis=m
        bpy.context.view_layer.update()
        for side,sign in [('L',-1),('R',1)]:
            pb=rig.pose.bones['B_'+side+'_UpperArm'];w=rig.matrix_world@pb.matrix;t=w.translation.copy()
            w=Matrix.Rotation(sign*math.radians(spread),4,'Y')@w;w.translation=t
            pb.matrix=rig.matrix_world.inverted()@w;bpy.context.view_layer.update()
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        floor=min((body.matrix_world@v.co).z for v in mesh.vertices);ev.to_mesh_clear()
        lift=max(0,.003-floor);pb=rig.pose.bones['B_Pelvis'];w=rig.matrix_world@pb.matrix;w.translation.z+=lift
        pb.matrix=rig.matrix_world.inverted()@w;bpy.context.view_layer.update()
        lifts.append(lift);poses.append(snapshot())
    if 'Walking' in name or 'Running' in name:poses[-1]=poses[0]
    if source==name: bpy.data.actions.remove(old)
    new=bpy.data.actions.new(name);new.use_fake_user=True;new_actions.append(new)
    action(new)
    for f,pose in enumerate(poses):
        for pb in rig.pose.bones:
            pb.matrix_basis=pose[pb.name];pb.rotation_mode='QUATERNION'
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    new.use_frame_range=True;new.frame_start=0;new.frame_end=n
    for layer in new.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    records[name]={'source':source,'duration':n/30,'arm_spread_degrees':spread,'max_floor_lift_m':max(lifts)}
    if name=='Drudge_Death':
        dead=bpy.data.actions.new('Drudge_Dead');dead.use_fake_user=True;new_actions.append(dead);action(dead)
        for f in [0,30]:
            for pb in rig.pose.bones:
                pb.matrix_basis=poses[-1][pb.name];pb.rotation_mode='QUATERNION'
                pb.keyframe_insert('rotation_quaternion',frame=f)
                if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
        dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
for old in list(bpy.data.actions):
    if old not in new_actions:bpy.data.actions.remove(old)
action(None)
for b in rig.pose.bones:b.matrix_basis=Matrix()
for o in bpy.data.objects:o.select_set(o in [rig,body])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'work/motion.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_skins=True,
 export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,
 export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion.blend'))
(P/'review/motion_authoring.json').write_text(json.dumps(records,indent=2)+'\n')
print('MOTION',records,flush=True);sys.stderr.flush();os._exit(0)
