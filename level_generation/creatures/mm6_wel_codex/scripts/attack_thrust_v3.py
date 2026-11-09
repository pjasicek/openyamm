"""Replace only Attack on the accepted v2 master with a point-led overhand thrust."""
import bpy, json, math, sys, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1]
V2=P/'review/revisions/water_v2'
OUT=P/'review/attack_thrust_v3'
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(V2/'work/textured_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
R={b.name:b.matrix_local.copy() for b in rig.data.bones}
GR=json.loads((P/'work/grip_pose.json').read_text())
ah=Vector(GR['handle_axis_hand_local']);gh=Vector(GR['handle_centre_hand_local'])
U,F,H='B_R_UpperArm','B_R_Forearm','B_R_Hand'
ru=R[F].translation-R[U].translation;rf=R[H].translation-R[F].translation
rn=ru.cross(rf);a,b=ru.length,rf.length

def ss(x):x=max(0,min(1,x));return x*x*(3-2*x)
def path(t,keys):
 for (start,p),(end,q) in zip(keys,keys[1:]):
  if t<=end:return Vector(p).lerp(Vector(q),ss((t-start)/(end-start)))
 return Vector(keys[-1][1])
def frame(a,b):
 a=a.normalized();b=(b-a*a.dot(b)).normalized();return Matrix((a,b,a.cross(b))).transposed()
def align(a,b,c,d):return frame(c,d)@frame(a,b).transposed()
def matrix(rot,pos):m=rot.to_4x4();m.translation=pos;return m
def curves(act):
 return [f for l in act.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
def action_hash(act):
 d=[(f.data_path,f.array_index,[(list(k.co),k.interpolation) for k in f.keyframe_points]) for f in curves(act)]
 return hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
unchanged={a.name:action_hash(a) for a in bpy.data.actions if a.name!='Attack'}
action=bpy.data.actions['Attack'];rig.animation_data.action=action
samples=[]
sc.frame_set(1);bpy.context.view_layer.update()
idle_arm={n:rig.pose.bones[n].matrix.copy() for n in [U,F,H]}
idle_local={n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy()) for n in [U,F,H]}
idle_chest=rig.pose.bones['B_Spine2'].matrix.copy()
for f in range(97):
 t=f/60;source_t=t if t<=1.02 else 1.02+(t-1.02)*(.33/.58)
 source_frame=source_t*60+1;sc.frame_set(int(source_frame),subframe=source_frame%1);bpy.context.view_layer.update()
 old={n:rig.pose.bones[n].matrix.copy() for n in [U,F,H]}
 # The submerged lower body stays anchored; the upper-body wind-up already contributes momentum.
 X=rig.pose.bones['B_Spine2'].matrix@R['B_Spine2'].inverted();cr=X.to_3x3()
 follow=rig.pose.bones['B_Spine2'].matrix@idle_chest.inverted()
 old={n:follow@idle_arm[n] for n in [U,F,H]}
 S=old[U].translation
 W=X@path(t,[(0,(-.465,-.163,1.148)),(.48,(-.51,.07,1.61)),(.68,(-.51,.09,1.61)),(1.02,(-.49,-.16,1.78)),(1.10,(-.49,-.16,1.78)),(1.35,(-.465,-.163,1.148))])
 pole=X@Vector((-.64,.08,1.32))
 v=W-S;distance=min(max(v.length,abs(a-b)+.002),a+b-.002);v.normalize();W=S+v*distance
 pp=pole-S;pp=(pp-v*v.dot(pp)).normalized();along=(a*a-b*b+distance*distance)/(2*distance)
 elbow=S+v*along+pp*math.sqrt(max(0,a*a-along*along));normal=(elbow-S).cross(W-elbow)
 Ra=align(ru,rn,elbow-S,normal)@R[U].to_3x3()
 Rf=align(rf,rn,W-elbow,normal)@R[F].to_3x3()
 natural=(cr@ru).rotation_difference(elbow-S).to_matrix()@cr@R[U].to_3x3()
 q=(natural.transposed()@Ra).to_quaternion();twist=(2*math.atan2(q.y,q.w)+math.pi)%(2*math.pi)-math.pi
 Ra=natural@Quaternion((0,1,0),max(-1.05,min(1.05,twist))).to_matrix()
 idleA=(idle_arm[H].to_3x3()@ah).normalized()
 aim=Vector((.025,-.985,-.17)).normalized()
 # Set the point before driving it; keep the shaft direction fixed through contact and extraction.
 fade=ss(t/.48)*ss((1.35-t)/.25)
 A=idleA.lerp(aim,fade).normalized()
 neutral=Rf@R[F].to_3x3().transposed()@R[H].to_3x3();fy=(W-elbow).normalized()
 source=neutral@ah;source=(source-fy*source.dot(fy)).normalized();target=A-fy*A.dot(fy)
 projection=target.length;target.normalize()
 roll=math.atan2(fy.dot(source.cross(target)),source.dot(target))
 Rf=Quaternion(fy,roll).to_matrix()@Rf
 neutral=Rf@R[F].to_3x3().transposed()@R[H].to_3x3();delta=(neutral@ah).rotation_difference(A)
 Rh=Quaternion().slerp(delta,min(1,math.radians(40)/max(delta.angle,1e-6))).to_matrix()@neutral
 # Every shoulder/elbow/wrist joint retains its fixed rest length.
 for n,rot in [(U,Ra),(F,Rf),(H,Rh)]:
  pb=rig.pose.bones[n]
  pos=pb.parent.matrix@pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local
  pb.matrix=matrix(rot,pos.translation)
  bpy.context.view_layer.update()
 samples.append({n:(rig.pose.bones[n].location.copy(),rig.pose.bones[n].rotation_quaternion.copy()) for n in R})
# Blend fixed endpoint poses, avoiding the shortest-arc branch change of moving targets.
for first,last,source,target in [(0,29,idle_local,samples[29]),(62,75,samples[62],samples[29]),(75,96,samples[29],idle_local)]:
 for f in range(first,last+1):
  w=ss((f-first)/(last-first))
  samples[f].update({n:(source[n][0].lerp(target[n][0],w),source[n][1].slerp(target[n][1],w)) for n in [U,F,H]})
# Sample first, write second: never use a just-modified key as the next frame's input.
for f,values in enumerate(samples):
 for n,(loc,q) in values.items():
  if f and q.dot(samples[f-1][n][1])<0:q.negate()
  pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=q
  for prop in ['location','rotation_quaternion']:pb.keyframe_insert(prop,frame=f+1,group=n)
for fc in curves(action):
 for k in fc.keyframe_points:k.interpolation='LINEAR'
assert unchanged=={a.name:action_hash(a) for a in bpy.data.actions if a.name!='Attack'}
(OUT/'authored_motion.json').write_text(json.dumps({'unchanged_actions':unchanged,'mechanics':'mechanics.json'},indent=2))
rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
rig.animation_data.action=action;common.workbench_clay(sc)
for f in [0,24,40,49,57,61,70,82,96]:
 sc.frame_set(f+1);common.render_views(str(OUT/f'clay_{f:02}'),1.1,3.8,views=('front','right'),resolution=(600,640),target=(0,-.45))
print('Attack-only thrust authored; other eight action hashes unchanged.',flush=True)
