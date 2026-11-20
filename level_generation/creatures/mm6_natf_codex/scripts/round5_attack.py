"""Attack-only follow-through repair and phase retiming; preserve the accepted other actions."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round5/before/work/accepted_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
side=Side('R');ac=bpy.data.actions['Attack'];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0]
changed=['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_R_UpperArmTwist','B_R_ForearmTwist'];samples=[]
for f in range(130):
 sc.frame_set(f);samples.append({n:rig.pose.bones[n].rotation_quaternion.copy()for n in changed})
def smooth(x):x=max(0,min(1,x));return max(0,min(1,x*x*x*(10+x*(-15+6*x))))
rows=[];prev=None
for f in range(130):
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];sc.frame_set(f);old=samples[f];t=f/60;w=smooth((t-.80)/.22)*(1-smooth((t-1.34)/.36))
 if w>0:
  S=rig.pose.bones['B_R_UpperArm'].head.copy();E=rig.pose.bones['B_R_Forearm'].head.copy();W=rig.pose.bones['B_R_Hand'].head.copy();Rh=rig.pose.bones['B_R_Hand'].matrix.to_3x3();target=W+Vector((.045,-.12,-.115))*w;axis=(target-S).normalized();pole=E-S;cands=[]
  for deg in range(-180,181,3):
   r=side.pose_anatomical(target,Rh,Quaternion(axis,math.radians(deg))@pole);base=rig.pose.bones['B_R_Clavicle'].matrix.to_3x3()@side.rel['Arm'];roll=abs(swing_twist_deg((base.inverted()@r['Ra']).to_quaternion(),side.uA)[1]);cost=roll*3+(r['E']-E).length*20
   if prev is not None:cost+=math.degrees(prev.rotation_difference(r['Ra'].to_quaternion()).angle)*.4
   cands.append((cost,r,roll))
  _,r,roll=min(cands,key=lambda x:x[0]);r['Rh']=r['Rf']@side.rel['Hand'];rig.animation_data.action=None;side.apply(r)
  for n in changed[:3]:rig.pose.bones[n].rotation_quaternion=old[n].slerp(rig.pose.bones[n].rotation_quaternion,w)
  bpy.context.view_layer.update()
  # Remove the old extreme follow-through twist without changing weights or other clips.
  q=rig.pose.bones['B_R_UpperArm'].rotation_quaternion;roll=swing_twist_deg(q,side.uA)[1]
  rig.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=old['B_R_UpperArmTwist'].slerp(Quaternion(side.uA,math.radians(-.5*roll)),w)
  rig.pose.bones['B_R_ForearmTwist'].rotation_quaternion=old['B_R_ForearmTwist'].slerp(Quaternion(),w)
  bpy.context.view_layer.update();prev=rig.pose.bones['B_R_UpperArm'].matrix.to_quaternion()
  # Interpolation of solutions must retain the signed anatomical hinge.
  U=rig.pose.bones['B_R_UpperArm'];F=rig.pose.bones['B_R_Forearm'];h=(U.matrix.to_3x3()@Vector((0,0,-1))).normalized();v=(F.matrix.to_3x3()@side.uF).normalized();d=(v-h*v.dot(h)).normalized();R=v.rotation_difference(d).to_matrix()@F.matrix.to_3x3();M=R.to_4x4();M.translation=F.head;F.matrix=M;bpy.context.view_layer.update()
  row={n:rig.pose.bones[n].rotation_quaternion.copy()for n in changed}
 else:row=old
 rows.append(row)
# Smooth the fitted shoulder/elbow solution, then restore its exact anatomical hinge.
filtered=[]
for i,row in enumerate(rows):
 t=i/60;blend=smooth((t-.80)/.10)*(1-smooth((t-1.60)/.10));dst={}
 for n in changed:
  ref=row[n];v=np.zeros(4)
  for k in range(-12,13):
   q=rows[max(0,min(129,i+k))][n];v+=np.array(q)*math.exp(-k*k/32)*(1 if q.dot(ref)>=0 else -1)
  dst[n]=ref.slerp(Quaternion(v/np.linalg.norm(v)),blend)
 filtered.append(dst)
for f,row in enumerate(filtered):
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];sc.frame_set(f);rig.animation_data.action=None
 for n,q in row.items():rig.pose.bones[n].rotation_quaternion=q
 bpy.context.view_layer.update()
 if .80<f/60<1.70:
  U=rig.pose.bones['B_R_UpperArm'];F=rig.pose.bones['B_R_Forearm'];h=(U.matrix.to_3x3()@Vector((0,0,-1))).normalized();v=(F.matrix.to_3x3()@side.uF).normalized();d=(v-h*v.dot(h)).normalized();M=(v.rotation_difference(d).to_matrix()@F.matrix.to_3x3()).to_4x4();M.translation=F.head;F.matrix=M;bpy.context.view_layer.update();row[F.name]=F.rotation_quaternion.copy()
rows=filtered
rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];last={}
for f,row in enumerate(rows):
 for n,q in row.items():
  if n in last and q.dot(last[n])<0:q=-q
  last[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
# Exact 1.3x wind-up and recovery, original-speed strike. Frame ids are the viewer's 48 Hz ids.
a=27/48;b=64/48;old_end=2.15
warp=lambda t:t/1.3 if t<=a else a/1.3+t-a if t<=b else a/1.3+b-a+(t-b)/1.3
end=warp(old_end);export_end=math.ceil(end*60)/60
for layer in ac.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.co.x=warp(k.co.x/60)*60;k.interpolation='LINEAR'
    fc.update();value=fc.evaluate(end*60);fc.keyframe_points.insert(export_end*60,value,options={'FAST'});fc.update()
ac.use_frame_range=True;ac.frame_start=0;ac.frame_end=export_end*60
report={'source_fps':48,'speed_multiplier':1.3,'original_duration_s':old_end,'exact_retimed_duration_s':end,'export_duration_s':export_end,'endpoint_padding_s':export_end-end,'windup_end_s':warp(a),'recovery_start_s':warp(b),'expected_impact_s':warp(.6979166666666666),'fix_original_time_window_s':[.80,1.70],'changed_bones':changed}
(P/'review/round5/timing.json').write_text(json.dumps(report,indent=2));rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/accepted_master.blend'));print('ROUND5',json.dumps(report),flush=True)
import runpy
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
