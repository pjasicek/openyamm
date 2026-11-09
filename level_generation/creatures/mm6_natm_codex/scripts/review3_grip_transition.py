"""Smooth the grasp, then open distal fingers while the palm remains seated for release."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
lg=json.loads((P/'work/round3_left_grip.json').read_text());D=json.loads((P/'work/round3_pose_reference.json').read_text());rows=[]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig']
for f in range(109):C.activate('Attack',f/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
for _ in range(5):
 old=[dict(row)for row in rows]
 for f in range(33,40):
  for part in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
   n='B_L_'+part;ref=old[f][n].to_quaternion();total=np.zeros(4)
   for delta,w in [(-2,1),(-1,4),(0,6),(1,4),(2,1)]:
    q=old[max(32,min(40,f+delta))][n].to_quaternion()
    if ref.dot(q)<0:q.negate()
    total+=np.array(q)*w
   q=Quaternion(total);q.normalize();m=q.to_matrix().to_4x4();m.translation=old[f][n].translation;rows[f][n]=m
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in range(33,40):
  for part in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
   n='B_L_'+part;b=r.pose.bones[n];b.matrix_basis=rows[f][n];b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 for f in range(57,85):
  for n,q in lg['finger_local'].items():
   base=Matrix(D['standing_basis'][n]).to_quaternion();start,end=(56,60)if len(n)>len('B_L_Finger0')else(60,72);t=max(0,min(1,(f-start)/(end-start)));t=t*t*(3-2*t);b=r.pose.bones[n];b.rotation_quaternion=Quaternion(q).slerp(base,t);b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
