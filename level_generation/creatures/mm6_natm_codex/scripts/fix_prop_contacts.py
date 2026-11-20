"""Library fall/cast correction with anatomical arms and a straight shield-side wrist."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/cloth_stable.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
sides={s:Side(s)for s in 'LR'};G=json.loads((P/'work/grip_pose.json').read_text());records={}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def helper(sd):
 fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=swing_twist_deg(rel@rr.inverted(),seg)[1];rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(seg,math.radians(max(-85,min(85,.65*tw))))
 ub=rig.data.bones[f'B_{sd}_UpperArm'];ax=(ub.matrix_local.inverted()@fb.head_local).normalized();uw=swing_twist_deg(rig.pose.bones[ub.name].rotation_quaternion,ax)[1];rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*uw));bpy.context.view_layer.update()
def fit(sd,W,R):
 obj=sides[sd];S=rig.pose.bones[f'B_{sd}_UpperArm'].head.copy();E=rig.pose.bones[f'B_{sd}_Forearm'].head.copy();pole=E-S;axis=(W-S).normalized();options=[]
 for deg in range(-120,121,5):
  r=obj.pose_anatomical(W+R@obj.grip_hand,R,Quaternion(axis,math.radians(deg))@pole)
  parent=rig.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@obj.rel['Arm'];upper=swing_twist_deg((parent.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]
  cost=.2*abs(deg)+.12*abs(upper)+.12*abs(r['tw'])+.3*r['sw']+8*max(0,abs(upper)-85)+5*max(0,abs(r['tw'])-110)+5*max(0,r['sw']-65)+r['miss']*1000
  options.append((cost,r))
 r=min(options,key=lambda x:x[0])[1];obj.apply(r);helper(sd)
for name in ['Cast','Death']:
 act=bpy.data.actions[name];last=int(act.frame_range[1]);out=[]
 for f in range(last+1):
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(f);rig.animation_data.action=None
  u=f/last;fade=smooth(f/8)*(1 if name=='Death' else smooth((last-f)/8))
  # Shield is strapped to the forearm, so a folded wrist must not enter its rim.
  hp=rig.pose.bones['B_L_Hand'];R0=hp.matrix.to_3x3();straight=rig.pose.bones['B_L_Forearm'].matrix.to_3x3()@sides['L'].rel['Hand'];R=R0.to_quaternion().slerp(straight.to_quaternion(),fade).to_matrix();W=hp.head.copy()
  if name=='Death':W.z+=.025*smooth((u-.45)/.2)
  fit('L',W,R)
  if name=='Death':
   hp=rig.pose.bones['B_R_Hand'];W=hp.head.copy();R=hp.matrix.to_3x3();W.x=min(W.x,rig.pose.bones['B_Pelvis'].head.x-.50-(R@Vector(G['handle_centre_hand_local'])).x*fade)
   axis=R@Vector(G['handle_axis_hand_local']);want=Vector((0,-1,axis.z)).normalized();R=axis.rotation_difference(axis.lerp(want,fade).normalized()).to_matrix()@R
   for it in range(3):
    W.x=min(W.x,rig.pose.bones['B_Pelvis'].head.x-.48-(R@Vector(G['handle_centre_hand_local'])).x)
    S=rig.pose.bones['B_R_UpperArm'].head;available=max(.02,(sides['R'].l1+sides['R'].l2)*.985-abs(W.x-S.x));W.y=S.y+max(-available,min(available,W.y-S.y))
    centre=W+R@Vector(G['handle_centre_hand_local']);axis=R@Vector(G['handle_axis_hand_local']);az=max(-.85,min(.85,axis.z));az=max(-(centre.z-.035)/1.08,min((centre.z-.035)/.89,az));flat=Vector((axis.x,axis.y,0)).normalized();want=flat*math.sqrt(max(0,1-az*az))+Vector((0,0,az));R=axis.rotation_difference(want).to_matrix()@R
    fit('R',W,R)
    ob=bpy.data.objects['SpearMesh'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();floor=min(v.co.z for v in me.vertices);ev.to_mesh_clear()
    if floor>=.002:break
    W.z+=.003-floor
  pose={pb.name:(pb.location.copy(),pb.rotation_quaternion.copy())for pb in rig.pose.bones};out.append(pose)
 for f,pose in enumerate(out):
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for n,(l,q)in pose.items():
   if any(n.startswith(f'B_{s}_')and any(k in n for k in ('UpperArm','Forearm','Hand'))for s in 'LR'):
    pb=rig.pose.bones[n];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 records[name]=out
act=bpy.data.actions['Dead'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in [0,1]:
 for n,(l,q)in records['Death'][-1].items():
  pb=rig.pose.bones[n];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    groups={}
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
     if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
    for comps in groups.values():
     if len(comps)!=4:continue
     prev=None;keys=[comps[i].keyframe_points for i in range(4)]
     for j in range(min(map(len,keys))):
      q=[keys[i][j].co.y for i in range(4)]
      if prev is not None and sum(x*y for x,y in zip(prev,q))<0:
       for i in range(4):keys[i][j].co.y*=-1
       q=[-v for v in q]
      prev=q
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/contact_master.blend'))
