"""Keep both fitted fists on the long sword handle while preserving the mocap elbow plane."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import armik,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fingers.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.loads((P/f'work/grip_pose{"" if s=="R" else "_L"}.json').read_text()) for s in 'RL'}
C={s:Vector(g['handle_centre_hand_local']) for s,g in G.items()};A={s:Vector(g['handle_axis_hand_local']) for s,g in G.items()}
def setact(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def apply(p):
    for n,(q,l) in p.items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
    bpy.context.view_layer.update()
setact(bpy.data.actions['Standing']);sc.frame_set(0);idle=snap();report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Cast']:
    ac=bpy.data.actions[name];n=int(ac.frame_range[1]);poses=[];errors=[];reach=[];angles=[]
    for f in range(n+1):
        setact(ac);sc.frame_set(f);pose=snap();setact(None);apply(pose)
        if name=='Cast':
            for b in ('Clavicle','UpperArm','Forearm','Hand'):
                bn=f'B_R_{b}';rig.pose.bones[bn].rotation_quaternion=idle[bn][0]
            bpy.context.view_layer.update()
        for side in 'RL':
            if side=='L' and name=='Cast':
                for bn in G[side]['finger_local']:rig.pose.bones[bn].rotation_quaternion=Quaternion().slerp(pose[bn][0],.25)
                continue
            for bn,q in G[side]['finger_local'].items():rig.pose.bones[bn].rotation_quaternion=Quaternion(q)
        bpy.context.view_layer.update()
        if name not in ('Cast','Death'):
            mr=armik.W(rig,'B_R_Hand')
            if name=='Attack':
                centre=(rig.pose.bones['B_L_UpperArm'].head+rig.pose.bones['B_R_UpperArm'].head)*.5
                torso=rig.pose.bones['B_Spine2'].matrix.to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()
                front=torso@Vector((0,-1,0));front.z=0;front.normalize()
                t=max(0,min(1,(.48-(mr.translation-centre).length)/.16));t=t*t*(3-2*t)
                target=mr.translation+front*(.13*t)
                armik.solve(rig,'R',target,hand_rot=mr.to_3x3().normalized());mr=armik.W(rig,'B_R_Hand')
            if name=='Running':
                shoulder=armik.W(rig,'B_L_UpperArm').translation
                target=mr.translation+(shoulder-mr.translation).normalized()*.055
                armik.solve(rig,'R',target,hand_rot=mr.to_3x3().normalized())
                mr=armik.W(rig,'B_R_Hand')
            ml=armik.W(rig,'B_L_Hand')
            d=(mr.to_3x3()@A['R']).normalized();old=(ml.to_3x3()@A['L']).normalized()
            rot=old.rotation_difference(d).to_matrix()@ml.to_3x3().normalized()
            target=mr@C['R']-d*.115
            rw=target-rot@C['L'];rr=armik.solve(rig,'L',rw,hand_rot=rot)
            if name!='Death' or f<=6:
                errors.append((armik.W(rig,'B_L_Hand')@C['L']-target).length);reach.append(rr)
            if name=='Death' and f>6:
                t=min(1,(f-6)/9);t=t*t*(3-2*t)
                for b in ('UpperArm','Forearm','Hand'):
                    bn=f'B_L_{b}';pb=rig.pose.bones[bn];pb.rotation_quaternion=pb.rotation_quaternion.slerp(pose[bn][0],t)
                bpy.context.view_layer.update()
            angles.append(math.degrees(old.angle(d)))
        if name=='Death':
            t=max(0,min(1,(f-9)/9));t=t*t*(3-2*t)
            for side in 'RL':
                for bn,q in G[side]['finger_local'].items():rig.pose.bones[bn].rotation_quaternion=Quaternion(q).slerp(Quaternion(),t*.8)
            bpy.context.view_layer.update()
        poses.append(snap())
    setact(ac);prev={}
    for f,p in enumerate(poses):
        for bn,(q,l) in p.items():
            if bn in prev and q.dot(prev[bn])<0:q=-q
            prev[bn]=q;b=rig.pose.bones[bn];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
            if bn=='B_Pelvis':b.keyframe_insert('location',frame=f)
    report[name]={'max_grip_error_mm':max(errors,default=0)*1000,'max_reach_ratio':max(reach,default=0),'source_axis_correction_max_deg':max(angles,default=0)}
    print('TWO_HAND',name,report[name],flush=True)
setact(None)
(P/'work/two_hand_fit.json').write_text(json.dumps(report,indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_gripped.blend'))
