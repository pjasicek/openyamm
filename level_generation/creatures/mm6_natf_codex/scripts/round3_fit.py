import bpy,sys,json,math,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_motion.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0);guard=rig.pose.bones['B_L_Hand'].matrix.copy();rig.animation_data.action=None
blade_inv=rig.data.bones['B_R_Forearm'].matrix_local.inverted();blade_local=np.array([tuple(blade_inv@v.co)for v in bpy.data.objects['ForearmBlade'].data.vertices]);sides={s:Side(s)for s in 'LR'};roles=['Running','Attack'];names=list(rig.pose.bones.keys())
def attach(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def apply(p):
 attach(None)
 for n,(q,l)in p.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l
 bpy.context.view_layer.update()
def smooth(seq,i,sigma):
 ref=seq[i];v=np.zeros(4)
 for k in range(-int(3*sigma),int(3*sigma)+1):
  q=seq[(i+k)%(len(seq)-1)if role in ['Walking','Running']else min(len(seq)-1,max(0,i+k))];v+=np.array(q)*math.exp(-k*k/(2*sigma*sigma))*(1 if q.dot(ref)>=0 else -1)
 return Quaternion(v/np.linalg.norm(v))
allposes={}
for role in roles:
 ac=bpy.data.actions[role];attach(ac);samples=[]
 for f in range(int(ac.frame_range[1])+1):sc.frame_set(f);samples.append(snap())
 smoothnames=[n for n in names if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']or any(n==f'B_{s}_{x}'for s in 'LR'for x in ['Clavicle','UpperArm','Forearm','Hand'])]
 seq={n:[p[n][0]for p in samples]for n in smoothnames};prev={};rows=[]
 for i,p in enumerate(samples):
  p=p.copy()
  if role in ['Attack','Hit','Death']:
   for n in smoothnames:p[n]=(smooth(seq[n],i,3 if role!='Death'else 2.5),p[n][1])
  apply(p)
  for sd in 'LR':
   # Both arms keep their anatomical hinge after world-space carry adjustments.
   obj=sides[sd];S=rig.pose.bones[f'B_{sd}_UpperArm'].head.copy();H=rig.pose.bones[f'B_{sd}_Hand'].matrix.copy();T=H.translation.copy();R=H.to_3x3();F0=rig.pose.bones[f'B_{sd}_Forearm'].matrix.to_3x3();E0=rig.pose.bones[f'B_{sd}_Forearm'].head.copy();pole=E0-S;axis=(T-S).normalized();cands=[]
   if role=='Death':
    t=i/60;settle=max(0,min(1,t/.15 if sd=='R'else (t-.12)/.28));settle=settle*settle*(3-2*settle)
    T.z=T.z*(1-settle)+(max(.16,S.z+.04)if sd=='R'else .16)*settle
   if sd=='R' and role!='Attack':
    spread=max(0,min(1,i/60/.35)) if role=='Death'else 0;spread=spread*spread*(3-2*spread)
    T.x=min(T.x,(-.40-.20*spread if role=='Death'else -.35)if T.z<1.0 else -.24)
   if sd=='L' and role in ['Attack','Cast']:T.x=max(T.x,.40)
   if role=='Running' and sd=='L':
    T=guard.translation+Vector((.15,.07*math.sin(math.tau*i/48),-.07+.02*math.cos(math.tau*i/48)));R=Matrix.Rotation(math.radians(10*math.sin(math.tau*i/48)),3,'X')@guard.to_3x3()
   if role=='Attack' and sd=='R':T=Vector(json.loads((P/'review/round3/attack_targets.json').read_text())['Attack'][i]['wrist'])
   axis=(T-S).normalized()
   for deg in range(-180,181,5):
    r=obj.pose_anatomical(T,R,Quaternion(axis,math.radians(deg))@pole)
    base=rig.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@obj.rel['Arm'];roll=abs(swing_twist_deg((base.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]);hb=r['Rf']@obj.rel['Hand'];ax=(hb.inverted()@(r['W']-r['E'])).normalized();sw,tw=swing_twist_deg((hb.inverted()@R).to_quaternion(),ax)
    share=max(-89,min(89,tw*.8));r['Rf']=Quaternion((r['W']-r['E']).normalized(),math.radians(share if sd=='L' or role not in ['Attack','Hit','Death'] else 0)).to_matrix()@r['Rf']
    if sd=='R' and role in ['Attack','Hit','Death']:
     ft=swing_twist_deg((r['Rf'].inverted()@F0).to_quaternion(),obj.uF)[1]
     if role=='Attack':
      t=i/60;w=max(0,min(1,(t-.45)/.15))*max(0,min(1,(1.12-t)/.25));w=w*w*(3-2*w);ft+=18*w
     r['Rf']=Quaternion((r['W']-r['E']).normalized(),math.radians(max(-89,min(89,ft)))).to_matrix()@r['Rf'];r['Rh']=r['Rf']@obj.rel['Hand']
    floor_cost=max(0,.02-float((blade_local@np.array(r['Rf']).T+np.array(r['E']))[:,2].min()))*10000 if role=='Death'and sd=='R'else 0
    cost=floor_cost+(max(0,.09-r['E'].z)*5000 if role=='Death'else 0)+(r['E']-E0).length*20+max(0,roll-52)*20+roll*.05
    if sd=='L' or role not in ['Attack','Hit','Death']:cost+=max(0,abs(tw-share)-38)*30+max(0,sw-60)*25
    if sd in prev:
     delta=math.degrees(prev[sd].rotation_difference(r['Ra'].to_quaternion()).angle);cost+=delta*.7+max(0,delta-7)*40
    cands.append((cost,r,roll))
   safe=[x for x in cands if x[2]<=55 and (role!='Death'or x[1]['E'].z>=.08)];assert safe,(role,sd,i,min(x[2]for x in cands));_,best,_=min(safe,key=lambda x:x[0]);obj.apply(best);prev[sd]=best['Ra'].to_quaternion()
   # Bound the wrist in the same fitted hand frame used by the runtime gate.
   if sd=='L':
    F=rig.pose.bones['B_L_Forearm'].matrix.to_3x3();H=rig.pose.bones['B_L_Hand'];base=F@obj.rel['Hand'];axis_h=(np.mean([np.array(rig.data.bones[f'B_L_Finger{k}'].head_local)for k in range(5)],axis=0)-np.array(rig.data.bones['B_L_Hand'].head_local));axis_h=(rig.data.bones['B_L_Hand'].matrix_local.to_3x3().inverted()@Vector(axis_h)).normalized();q=(base.inverted()@H.matrix.to_3x3()).to_quaternion();sw,tw=swing_twist_deg(q,axis_h);twq=Quaternion(axis_h,math.radians(tw));swing=q@twq.inverted();swing=swing if sw<=64 else Quaternion().slerp(swing,64/sw);R=base@(swing@Quaternion(axis_h,math.radians(max(-40,min(40,tw))))).to_matrix();M=R.to_4x4();M.translation=H.head;H.matrix=M;bpy.context.view_layer.update()
  rows.append(snap())
 allposes[role]=rows
# Smooth the bounded anatomical solutions together, retaining continuous source motion.
for role,rows in allposes.items():
 seq={n:[p[n][0]for p in rows]for n in names if any(n==f'B_{sd}_{k}'for sd in 'LR'for k in ['Clavicle','UpperArm','Forearm','Hand'])}
 for i,row in enumerate(rows):
  for n,qs in seq.items():row[n]=(smooth(qs,i,10 if role=='Death'else (4 if role=='Attack'else 3)),row[n][1])
# Quaternion filtering must preserve the anatomical elbow plane.
for row in allposes['Attack']:
 apply(row)
 for sd in 'LR':
  U=rig.pose.bones[f'B_{sd}_UpperArm'];F=rig.pose.bones[f'B_{sd}_Forearm'];h=(U.matrix.to_3x3()@Vector((0,0,-1))).normalized();v=(F.matrix.to_3x3()@sides[sd].uF).normalized();target=v-h*v.dot(h);assert target.length>.1;R=v.rotation_difference(target.normalized()).to_matrix()@F.matrix.to_3x3();M=R.to_4x4();M.translation=F.head;F.matrix=M;bpy.context.view_layer.update();row[F.name]=(F.rotation_quaternion.copy(),F.location.copy())
# Trim the quiet first tenth of the attack; the native blow now fits its 0.75 s wind-up.
# Preserve the requested wind-up timing.
# Other roles remain byte-for-byte in the authoring actions.
for role,rows in allposes.items():
 a=bpy.data.actions[role];bpy.data.actions.remove(a);a=bpy.data.actions.new(role);a.use_fake_user=True;attach(a);prev={}
 for f,row in enumerate(rows):
  for n,(q,l)in row.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
ns=runpy.run_path(str(P/'scripts/bake_twist.py'))
for a in bpy.data.actions:
 if a.name in roles:ns['bake_twist'](a)
# A fitted forearm already carries roll; bound the helper's combined roll, not just its additive channel.
for a in bpy.data.actions:
 if a.name not in roles:continue
 attach(a)
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f)
  for sd in 'LR':
   obj=sides[sd];U=rig.pose.bones[f'B_{sd}_UpperArm'];F=rig.pose.bones[f'B_{sd}_Forearm'];base=U.matrix.to_3x3()@obj.rel['ForeArm'];roll=swing_twist_deg((base.inverted()@F.matrix.to_3x3()).to_quaternion(),obj.uF)[1];pb=rig.pose.bones[f'B_{sd}_ForearmTwist'];extra=swing_twist_deg(pb.rotation_quaternion,obj.uF)[1];total=max(-85,min(85,roll+extra));pb.rotation_quaternion=Quaternion(obj.uF,math.radians(total-roll));pb.keyframe_insert('rotation_quaternion',frame=f)
attach(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3_fitted.blend'))
