"""Smooth the short combat transitions and align the cutting edge with the measured blow."""
import bpy,sys,math
import numpy as np
from pathlib import Path
from mathutils import Quaternion,Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/master_uv_fitted.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[b.name for b in rig.pose.bones]
def activate(a):
 rig.animation_data.action=a
 if a:rig.animation_data.action_slot=a.slots[0]
def snap():return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def apply(pose):
 activate(None)
 for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
def write(a,poses,step=1):
 activate(a);prev={}
 for f,pose in enumerate(poses):
  for n,(q,l) in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f*step)
for name,passes in [('Attack',6),('Hit',3),('Fidget',2)]:
 a=bpy.data.actions[name];activate(a);poses=[]
 for f in range(int(a.frame_range[1])+1):sc.frame_set(f);poses.append(snap())
 for it in range(passes):
  old=poses;poses=[dict(x) for x in old]
  for f in range(1,len(old)-1):
   for n in names:
    if any(k in n for k in ['Pelvis','Thigh','Calf','Foot','Toe','Finger','Sword']):continue
    q,l=old[f][n];qa=old[f-1][n][0];qb=old[f+1][n][0]
    if q.dot(qa)<0:qa=-qa
    if q.dot(qb)<0:qb=-qb
    poses[f][n]=(q.slerp(qa.slerp(qb,.5),.5),l)
 write(a,poses)
# Reduce the excess flight introduced by fitting the source feet to the shorter armoured legs.
a=bpy.data.actions['Running'];activate(a);poses=[]
feet=np.array([v.co.z<.09 and body.data.attributes['piece'].data[v.index].value in (0,2) for v in body.data.vertices])
for f in range(int(a.frame_range[1])+1):
 sc.frame_set(f);pose=snap();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v,keep in zip(me.vertices,feet) if keep);ev.to_mesh_clear()
 apply(pose);drop=max(0,low-.006)*.9
 if drop:
  for sd in 'LR':
   th,ca,ft=[f'B_{sd}_{x}' for x in ['Thigh','Calf','Foot']];H,K,A=[armik.W(rig,n).translation.copy() for n in [th,ca,ft]];R=armik.W(rig,ft).to_3x3();T=A-Vector((0,0,drop));d=T-H;u=d.normalized();L1=(K-H).length;L2=(A-K).length;dist=min(d.length,(L1+L2)*.999);bend=K-H;v=(bend-u*bend.dot(u)).normalized();c=(L1*L1+dist*dist-L2*L2)/(2*L1*dist);N=H+L1*(u*c+v*math.sqrt(max(0,1-c*c)))
   for bone,target in [(th,N),(ca,H+u*dist)]:
    M=armik.W(rig,bone);direction=target-M.translation;Q=(M.to_3x3()@Vector((0,1,0))).rotation_difference(direction);armik.set_world(rig,bone,armik.rot_world(M,Q.to_matrix()@M.to_3x3()))
   armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),R))
 poses.append(snap());activate(a)
poses[-1]=poses[0];write(a,poses)
# Fit clavicle travel to the rigid cuirass while retaining the weapon-hand path.
activate(bpy.data.actions['Standing']);sc.frame_set(0);guard=snap()
chest_rest=rig.data.bones['B_Spine2'].matrix_local
G=chest_rest@rig.pose.bones['B_Spine2'].matrix.inverted()
guard_wrist=G@rig.pose.bones['B_R_Hand'].head
guard_elbow=G@rig.pose.bones['B_R_Forearm'].head
guard_hand=G.to_3x3()@rig.pose.bones['B_R_Hand'].matrix.to_3x3()
for a in [a for a in bpy.data.actions if a.use_fake_user]:
 activate(a);poses=[];N=int(a.frame_range[1])
 originals=[]
 for f in range(N*4+1):sc.frame_set(f//4,subframe=(f%4)/4);originals.append(snap())
 for i,pose in enumerate(originals):
  f=i/4
  apply(pose);D=rig.pose.bones['B_Spine2'].matrix@chest_rest.inverted()
  for sd in 'LR':
   cl,ua,fa,hd=[f'B_{sd}_{n}' for n in ['Clavicle','UpperArm','Forearm','Hand']]
   wrist=armik.W(rig,hd).translation.copy();pole=armik.W(rig,fa).translation.copy();hand=armik.W(rig,hd).to_3x3()
   if a.name=='Attack' and sd=='R':
    # A free hand balances the cut in front of the hip; it does not follow the source's shield-arm sweep.
    t=math.sin(math.pi*f/N)**2
    for n in [cl,ua,fa,hd]:rig.pose.bones[n].rotation_quaternion=guard[n][0]
    bpy.context.view_layer.update()
    wrist=D@(guard_wrist+Vector((-.01,-.14,.18))*t)
    pole=D@(guard_elbow+Vector((-.025,.03,-.02))*t)
    hand=D.to_3x3()@guard_hand
   M=armik.W(rig,cl);original=armik.W(rig,ua).translation-M.translation
   rest=D.to_3x3()@(rig.data.bones[ua].head_local-rig.data.bones[cl].head_local)
   factor=.8
   if sd=='L':
    # Keep a fully extended sword stroke reachable; the shoulder may travel when the blade needs it.
    length=(armik.W(rig,fa).translation-armik.W(rig,ua).translation).length+(wrist-armik.W(rig,fa).translation).length
    lo,hi=0.,factor
    for _ in range(20):
     mid=(lo+hi)*.5;candidate=M.translation+original.lerp(rest,mid).normalized()*original.length
     if (wrist-candidate).length<=length*.999:lo=mid
     else:hi=mid
    factor=lo
    if a.name in ['Attack','Death']:factor*=1-.8*math.sin(math.pi*f/N)**2
   target=original.lerp(rest,factor).normalized()*original.length
   if sd=='R':
    delta=target-original;wrist+=delta;pole+=delta
   Q=original.rotation_difference(target)
   armik.set_world(rig,cl,armik.rot_world(M,Q.to_matrix()@M.to_3x3()))
   if sd=='R':
    # Keep the relaxed glove clear of the thigh after moving the shoulder back into its socket.
    local=D.inverted()@wrist;clearance=max(0,min(1,(1.12-local.z)/.20));clearance=clearance*clearance*(3-2*clearance)
    wrist+=D.to_3x3()@Vector((-.045,-.055,.02))*clearance
    shoulder=armik.W(rig,ua).translation;elbow=armik.W(rig,fa).translation
    length=(elbow-shoulder).length+(armik.W(rig,hd).translation-elbow).length
    direction=wrist-shoulder
    if direction.length>length*.995:wrist=shoulder+direction.normalized()*length*.995
   reach=armik.solve(rig,sd,wrist,pole=pole if sd=='R' else None,hand_rot=hand)
   assert reach<1.001,(a.name,f,sd,reach)
   if a.name=='Attack' and sd=='R':
    pb=rig.pose.bones[hd];pb.rotation_quaternion=pb.rotation_quaternion.slerp(Quaternion(),t*.9)
    bpy.context.view_layer.update()
  poses.append(snap())
 # Remove short IK elbow-plane transients while retaining the shared guard endpoints.
 if a.name in ['Hit','Fidget','Death']:
  for _ in range(48):
   old=poses;poses=[dict(pose) for pose in old]
   for i in range(1,len(old)-1):
    for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand']:
     q,l=old[i][n];qa=old[i-1][n][0];qb=old[i+1][n][0]
     if q.dot(qa)<0:qa=-qa
     if q.dot(qb)<0:qb=-qb
     poses[i][n]=(q.slerp(qa.slerp(qb,.5),.5),l)
 for i,pose in enumerate(poses):
  apply(pose);D=rig.pose.bones['B_Spine2'].matrix@chest_rest.inverted()
  for sd in 'LR':
   ua,fa,hd=[f'B_{sd}_{n}' for n in ['UpperArm','Forearm','Hand']]
   # A chest-mounted plate hinges outward for a raised arm, but never pitches down with an arm swing.
   u=D.inverted()@rig.pose.bones[ua].head;el=D.inverted()@rig.pose.bones[fa].head
   sg=1 if sd=='L' else -1;v=el-u
   elevation=math.atan2(max(0,sg*v.x),-v.z)
   lift=max(0,elevation-math.radians(25))*.8
   R=Quaternion((0,1,0),-sg*lift).to_matrix()
   pivot=Vector((sg*.135,-.005,1.34));offset=pivot-R@pivot
   T=R.to_4x4();T.translation=offset
   pb=rig.pose.bones[f'B_{sd}_Pauldron'];pb.matrix=D@T@rig.data.bones[pb.name].matrix_local
   bpy.context.view_layer.update()
   # Helper rotations must be derived from the final arm, not independently smoothed source keys.
   ub,fb,hb=[rig.data.bones[n] for n in [ua,fa,hd]]
   axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
   _,tw=armik.split_swing_twist(rig.pose.bones[ua].matrix_basis.to_quaternion(),axis)
   rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*tw)
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   rel=(rig.pose.bones[fa].matrix.inverted()@rig.pose.bones[hd].matrix).to_quaternion()
   rest_rel=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
   _,tw=armik.split_swing_twist(rel@rest_rel.inverted(),axis)
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*tw)
  poses[i]=snap()
 write(a,poses,.25)
 # Pauldron pivots stay at the cuirass seam instead of inheriting the moving upper-arm origin.
 for f,pose in enumerate(poses):
  for sd in 'LR':
   pb=rig.pose.bones[f'B_{sd}_Pauldron'];pb.location=pose[pb.name][1];pb.keyframe_insert('location',frame=f/4)

# A 30 mm grip closes the measured palm/thumb gaps without changing their pose.
inv=rig.data.bones['Sword'].matrix_local.inverted();M=rig.data.bones['Sword'].matrix_local
for v in bpy.data.objects['SwordMesh'].data.vertices:
 c=inv@v.co
 if -.08<c.y<.10 and math.hypot(c.x,c.z)<.02:
  c.x*=1.25;c.z*=1.25;v.co=M@c
 if c.y<-.085:
  c.x*=.6;c.z*=.6;c.y=-.09+(c.y+.12)*.6;v.co=M@c
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 activate(a)
 for f in range(int(a.frame_range[1])*4+1):
  pb=rig.pose.bones['Sword'];pb.rotation_quaternion=Quaternion((0,1,0),math.radians(-60));pb.keyframe_insert('rotation_quaternion',frame=f/4)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
activate(None)
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/master_uv_fitted.blend'))
