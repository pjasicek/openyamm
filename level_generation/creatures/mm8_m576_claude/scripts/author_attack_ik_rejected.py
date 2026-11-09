"""Left overhand trident plunge: native lift, overhead aim, downward contact, recovery.
Mocap supplies torso counter-motion; fixed-length IK fits the weapon arm and counterbalancing free arm.
The tip is the pinky end of the reverse grip, as in the native standing/attack sequence.
"""
import bpy,sys,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G=json.loads((P.parent/'work/grip_pose.json').read_text());AX=-Vector(G['handle_axis_hand_local']).normalized()
def set_act(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snapshot(act,f):
    set_act(act);sc.frame_set(int(f),subframe=f-int(f))
    return {pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
standing=snapshot(bpy.data.actions['Standing'],0)
source=bpy.data.actions['Stab2'];end=float(source.frame_range[1])
# Wrist/direction keys in world metres. Contact at 1.00 s fits MM8's full one-second native action.
keys=[(0,(.34,-.12,1.02),(0,-.5,-.866)),(21,(.38,-.025,1.52),(0,-.93,.36)),
      (27,(.38,-.13,1.62),(0,-1,.02)),(33,(.38,-.40,1.06),(0,-.40,-.916)),
      (35,(.38,-.40,1.05),(0,-.40,-.916)),(48,(.34,-.12,1.02),(0,-.5,-.866))]
def target(f,k):
    i=next((i for i in range(len(keys)-1) if keys[i+1][0]>=f),len(keys)-2)
    a,b=keys[i],keys[i+1];t=smooth((f-a[0])/(b[0]-a[0]));return Vector(a[k]).lerp(Vector(b[k]),t)
frames=[]
for f in range(49):
    own=snapshot(source,end*f/48);w=smooth(f/8)*smooth((48-f)/10)
    set_act(None)
    for pb in rig.pose.bones:pb.matrix_basis=standing[pb.name]
    # Preserve source trunk rotation without carrying its underhand weapon motion.
    for n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
        a=standing[n].to_quaternion();b=own[n].to_quaternion()
        if a.dot(b)<0:b=-b
        rig.pose.bones[n].rotation_quaternion=a.slerp(b,.25*w)
    bpy.context.view_layer.update()
    lean=math.radians(10)*math.sin(math.pi*f/48)**2
    M=armik.W(rig,'B_Spine');t=M.translation.copy();M=Matrix.Rotation(lean,4,'X')@M;M.translation=t
    armik.set_world(rig,'B_Spine',M)
    # A modest shoulder counter-swing keeps the nearly straight free arm away from the chest.
    M=armik.W(rig,'B_R_UpperArm');t=M.translation.copy()
    M=Matrix.Rotation(-math.radians(18)*w,4,'X')@M;M.translation=t
    armik.set_world(rig,'B_R_UpperArm',M)
    pb=rig.pose.bones['B_R_Forearm']
    pb.rotation_quaternion=standing[pb.name].to_quaternion()@Quaternion((0,0,-1),math.radians(24)*w)
    bpy.context.view_layer.update()
    snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
    frames.append({'snap':snap,'wrist':target(f,1),'dir':target(f,2).normalized(),'elbow_min_x':.23})
choice=armik.arm_dp(rig,'L',frames,AX,phis=range(-180,181,10),twist_neutral=-25,k_twist=.6,k_dphi=1,k_dpsi=.8)
phi=np.degrees(np.unwrap(np.radians([c['phi'] for c in choice])));psi=np.degrees(np.unwrap(np.radians([c['psi'] for c in choice])))
k=np.array([1,2,3,2,1],float);k/=k.sum()
phi=np.convolve(np.pad(phi,2,mode='edge'),k,'valid');psi=np.convolve(np.pad(psi,2,mode='edge'),k,'valid')
poses=[];stats=[]
for i,fr in enumerate(frames):
    sw,tw=armik.apply_arm(rig,'L',fr['snap'],fr['wrist'],AX,fr['dir'],phi[i],psi[i]);stats.append((sw,tw))
    pose={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
    # Ease endpoint arm choices into the exact standing pose, preventing an action-start snap.
    w=smooth(i/5)*smooth((48-i)/8)
    for n in pose:
        a=standing[n].to_quaternion();b=pose[n].to_quaternion()
        if a.dot(b)<0:b=-b
        pose[n]=a.slerp(b,w).to_matrix().to_4x4();pose[n].translation=standing[n].translation.lerp(fr['snap'][n].translation,w)
    poses.append(pose)
old=bpy.data.actions.get('Attack')
if old:bpy.data.actions.remove(old)
act=bpy.data.actions.new('Attack');act.use_fake_user=True;set_act(act);prev={}
for f,pose in enumerate(poses):
    for n,M in pose.items():
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';q=M.to_quaternion()
        if n in prev and q.dot(prev[n])<0:q=-q
        prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
        if n=='B_Pelvis':pb.location=M.translation;pb.keyframe_insert('location',frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=48
set_act(None)
(P.parent/'work/attack_fit.json').write_text(json.dumps({'impact_seconds':1.0,'duration_seconds':1.6,'wrist_swing_max':max(x[0] for x in stats),'wrist_twist_range':[min(x[1] for x in stats),max(x[1] for x in stats)],'keys':keys,'choices':choice},indent=2))
print('ATTACK wrist swing/twist',max(x[0] for x in stats),min(x[1] for x in stats),max(x[1] for x in stats),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=out)
