from pathlib import Path
import bpy,sys,json,math
import numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_level.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;names=[b.name for b in rig.data.bones]
def set_act(a):
    rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
    set_act(a);sc.frame_set(int(f),subframe=f-int(f))
    return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(pose):
    set_act(None)
    for n,(q,l) in pose.items():
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
    bpy.context.view_layer.update()
def blend(a,b,t):
    return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in names}
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def write(name,poses):
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    a=bpy.data.actions.new(name);a.use_fake_user=True;set_act(a);previous={}
    for f,pose in enumerate(poses):
        for n,(q,l) in pose.items():
            if n in previous and q.dot(previous[n])<0:q=-q
            previous[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
    set_act(None);return a
def points():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();return co
stand=sample(bpy.data.actions['Standing'],0)
g=json.loads((p/'work/grip_pose.json').read_text());tip_local=Vector(g['handle_centre_hand_local'])+Vector(g['handle_axis_hand_local'])*.59
attack=bpy.data.actions['Attack'];poses=[sample(attack,f) for f in range(int(attack.frame_range[1])+1)]
tips=[]
for pose in poses:
    apply(pose);tips.append(np.array(rig.pose.bones['B_R_Hand'].matrix@tip_local))
tips=np.array(tips);speed=np.linalg.norm(np.diff(tips,axis=0),axis=1)
# A cut contacts at maximum forward tip speed; the initial draw-back is excluded.
candidates=[i for i in range(len(speed)) if min(tips[i,1],tips[i+1,1]) < -.30]
assert candidates
impact_frame=max(candidates,key=lambda i:speed[i])+.5
lead=max(0,int(round((1.125-impact_frame/30)*30)))
ready=[blend(stand,poses[0],smooth(i/max(1,lead))) for i in range(lead)]
for i in range(len(poses)):
    if i>len(poses)-7:poses[i]=blend(poses[i],stand,smooth((i-(len(poses)-7))/6))
write('Attack',ready+poses)
report={'attack_native_impact_s':1.125,'source_impact_s':impact_frame/30,'attack_lead_s':lead/30,'attack_impact_s':(lead+impact_frame)/30,'attack_duration_s':(lead+len(poses)-1)/30}
for name,fade_in,fade_out in [('Hit',.10,.12),('Fidget',.25,.25),('Death',.20,0)]:
    a=bpy.data.actions[name];frames=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
    res=[]
    for i,pose in enumerate(frames):
        w=min(smooth(i/(fade_in*30)),smooth((len(frames)-1-i)/(fade_out*30)) if fade_out else 1)
        res.append(blend(stand,pose,w))
    write(name,res)
# Re-bake twist after the measured wrist correction, without transferring weights twice.
FA=.6;UA=.35
exec(compile('def twist_about'+(p/'scripts/twist_bones.py').read_text().split('def twist_about',1)[1].split('for act in [a for a in bpy.data.actions',1)[0],str(p/'scripts/twist_bones.py'),'exec'))
for a in [a for a in bpy.data.actions if a.use_fake_user]:bake_twist(a)
# Let the tail fall beside the corpse instead of staying rigidly vertical.
a=bpy.data.actions['Death'];death=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
for f,pose in enumerate(death):
    apply(pose);w=smooth((f-6)/15)
    for i in range(8):
        b=rig.pose.bones['Tail'+str(i)];m=b.matrix.copy();head=m.translation.copy();length=b.bone.length
        z=max(-.70,min(.20,(.035-head.z)/length));heading=.5+i*.12
        target=Vector((math.cos(heading)*math.sqrt(1-z*z),math.sin(heading)*math.sqrt(1-z*z),z))
        current=(m.to_3x3()@Vector((0,1,0))).normalized();q=Quaternion().slerp(current.rotation_difference(target),w)
        new=(q.to_matrix()@m.to_3x3()).to_4x4();new.translation=head;b.matrix=new;bpy.context.view_layer.update()
        pose[b.name]=(b.rotation_quaternion.copy(),b.location.copy())
write('Death',death)
vg=[g.name for g in body.vertex_groups]
feet=np.array([sum(e.weight for e in v.groups if vg[e.group] in ('B_L_Foot','B_R_Foot'))>.5 for v in body.data.vertices])
report['floor']={}
for name in ('Standing','Walking','Running','Attack','Hit','Fidget','Death'):
    a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];low=[]
    for pose in poses:
        apply(pose);co=points();low.append(float(co[:,2].min() if name=='Death' else co[feet,2].min()))
    low=np.array(low);target=np.zeros(len(low))
    if name=='Running':target=np.clip(low-np.percentile(low,35),0,.06)
    shift=target-low
    for f,pose in enumerate(poses):
        apply(pose);pel=rig.pose.bones['B_Pelvis'];m=pel.matrix.copy();m.translation.z+=float(shift[f]);pel.matrix=m;bpy.context.view_layer.update()
        pose['B_Pelvis']=(pel.rotation_quaternion.copy(),pel.location.copy())
    write(name,poses);report['floor'][name]={'shift_cm':[float(shift.min()*100),float(shift.max()*100)],'flight_max_cm':float(target.max()*100)}
last=sample(bpy.data.actions['Death'],bpy.data.actions['Death'].frame_range[1]);write('Dead',[last,last])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
(p/'work/clip_timing.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_final.blend'))
print('TIMING',json.dumps(report))
