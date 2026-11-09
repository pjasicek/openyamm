"""Library motion adapted to the native relaxed carry; geometric foot and elbow constraints."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
sides={s:Side(s) for s in 'LR'};names=[b.name for b in rig.data.bones];FPS=48
G=json.loads((P/'work/grip_pose.json').read_text());FJ=json.loads((P/'work/finger_joints.json').read_text())
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def apply(p):
 setact(None)
 for n,(q,l) in p.items():pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def capture():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def sample(a,t):
 setact(a);f=max(0,min(float(a.frame_range[1]),t));sc.frame_set(int(f),subframe=f-int(f));return capture()
def wm(n):return rig.pose.bones[n].matrix.copy()
def pos(n):return rig.pose.bones[n].head.copy()
def put(n,R,location=None):
 pb=rig.pose.bones[n];m=R.to_4x4() if len(R)==3 else R.copy();m.translation=pos(n) if location is None else location;pb.matrix=m;bpy.context.view_layer.update()
def shiftpelvis(d):
 m=wm('B_Pelvis');m.translation+=d;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t))for n in names}
def aim(n,child,target):
 R=wm(n).to_3x3();u=(pos(child)-pos(n)).normalized();put(n,u.rotation_difference((target-pos(n)).normalized()).to_matrix()@R)
rest={n:rig.data.bones[n].matrix_local.copy()for n in names}
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
setact(None);bpy.context.view_layer.update()
co=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([d.value for d in body.data.attributes['piece'].data]);group={g.index:g.name for g in body.vertex_groups}
ground_ids=[v.index for v in body.data.vertices if pv[v.index]==0 and sum(g.weight for g in v.groups if any(k in group[g.group] for k in ('Arm','Forearm','Hand','Finger')))<.3]
soles={};footR={};anklez={};home={}
for sd in 'LR':
 ids=[v.index for v in body.data.vertices if pv[v.index]==0 and sum(g.weight for g in v.groups if group[g.group].startswith((f'B_{sd}_Foot',f'B_{sd}_Toe')))> .65]
 z=min(co[ids,2]);ids=[i for i in ids if co[i,2]<z+.012];soles[sd]=ids
 foot=f'B_{sd}_Foot';toe=f'B_{sd}_Toe0';d=rest[toe].translation-rest[foot].translation;yaw=math.atan2(d.x,-d.y)
 R=Matrix.Rotation(-yaw,3,'Z')@rest[foot].to_3x3();footR[sd]=R
 points=np.array([tuple(R@rest[foot].to_3x3().inverted()@(Vector(co[i])-rest[foot].translation))for i in ids]);anklez[sd]=-points[:,2].min()+.002
 home[sd]=Vector((.135 if sd=='L' else -.135,-.045,anklez[sd]))
# Actual knuckle direction and flexion side, in each fitted hand frame.
handframe={}
for sd in 'LR':
 inv=rest[f'B_{sd}_Hand'].inverted();w=rest[f'B_{sd}_Hand'].translation
 kn=[Vector(FJ[sd][f'B_{sd}_Finger{i}']) for i in (1,2,3,4)];f=(sum(kn,Vector())/4-w).normalized()
 tip=Vector(FJ[sd][f'B_{sd}_Finger22_tip']);q=tip-kn[1];n=q-f*q.dot(f)
 # Surface/reference confirms the palm is the inward side of the A-pose hand, toward +Y.
 across=kn[0]-kn[3];n=across.cross(f).normalized();distal=sum((Vector(FJ[sd][f'B_{sd}_Finger{i}2']) for i in (1,2,3,4)),Vector())/4-sum(kn,Vector())/4
 if n.dot(distal)<0:n=-n
 fl=(inv.to_3x3()@f).normalized();nl=(inv.to_3x3()@n).normalized();xl=fl.cross(nl).normalized();nl=xl.cross(fl).normalized();local=Matrix([xl,fl,nl]).transposed()
 handframe[sd]=(fl,nl,local)
 print('HAND FRAME',sd,'finger',list(fl),'palm',list(nl),flush=True)
def handrot(sd,palm=Vector((1,0,0)),finger=Vector((0,0,-1))):
 y=finger.normalized();z=(palm-y*palm.dot(y)).normalized();x=y.cross(z).normalized();z=x.cross(y).normalized();return Matrix([x,y,z]).transposed()@handframe[sd][2].inverted()
def leg(sd,T,R=None):
 th,ca,ft=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']];H=pos(th);K=pos(ca);A=pos(ft);a=(K-H).length;b=(A-K).length
 delta=T-H;dist=min(delta.length,(a+b)*.997);u=delta.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();x=(a*a+dist*dist-b*b)/(2*dist);kn=H+u*x+v*math.sqrt(max(0,a*a-x*x));aim(th,ca,kn);aim(ca,ft,H+u*dist);put(ft,R if R is not None else footR[sd]);rig.pose.bones[f'B_{sd}_Toe0'].rotation_quaternion=Quaternion();bpy.context.view_layer.update()

a=bpy.data.actions['Running'];n=round(a.frame_range[1]);poses=[sample(a,i)for i in range(n+1)];output=[];reach=[]
for i,p in enumerate(poses):
 apply(p);shiftpelvis(Vector((0,0,-.055)))
 for sd,off in [('L',0),('R',.5)]:
  ph=(i/n+off)%1;stance=.48;amp=(.32/.54)*1.55*stance/2
  if ph<stance:y=amp-2*amp*ph/stance;lift=0
  else:q=(ph-stance)/(1-stance);y=-amp+2*amp*smooth(q);lift=.13*math.sin(math.pi*q)
  T=home[sd].copy();T.y-=y;T.z+=lift;leg(sd,T);reach.append((pos(f'B_{sd}_Foot')-T).length)
 output.append(capture())
setact(a)
for i,p in enumerate(output):
 pb=rig.pose.bones['B_Pelvis'];pb.location=p['B_Pelvis'][1];pb.keyframe_insert('location',frame=i)
 for sd in 'LR':
  for part in ['Thigh','Calf','Foot','Toe0']:
   bn=f'B_{sd}_{part}';pb=rig.pose.bones[bn];pb.rotation_quaternion=p[bn][0];pb.keyframe_insert('rotation_quaternion',frame=i)
setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_lod0.blend'));(P/'review/stride.json').write_text(json.dumps({'walking_stride_m':.32/.54,'running_stride_m':(.32/.54)*1.55,'runtime_run_multiplier':1.55,'running_ik_error_max_m':max(reach)},indent=2));assert max(reach)<.003
