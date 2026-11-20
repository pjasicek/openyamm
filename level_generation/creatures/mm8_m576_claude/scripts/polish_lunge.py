"""Smooth the transferred torso and align measured tip speed with the native damage event."""
import bpy,sys,json,math,runpy
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lunge_candidate.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[b.name for b in rig.data.bones]
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def put(row):
 act(None)
 for n,m in row.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
a=bpy.data.actions['Attack'];end=float(a.frame_range[1]);frames=np.arange(0,end+.001,.25);rows=[]
for f in frames:
 act(a);sc.frame_set(int(f),subframe=float(f%1));rows.append(snap())
# Preserve the drive timing and give the heavy polearm a slower recovery.
original=rows;end=63.;frames=np.arange(0,end+.001,.25);rows=[]
for f in frames:
 t=f/30;st=float(np.interp(t,[0,1.15,2.1],[0,1.15,1.65]));fi=min(st*120,len(original)-1);i=int(fi);j=min(i+1,len(original)-1);w=fi-i;row={}
 for n in names:
  q=original[i][n].to_quaternion().slerp(original[j][n].to_quaternion(),w);m=q.to_matrix().to_4x4();m.translation=original[i][n].translation.lerp(original[j][n].translation,w);row[n]=m
 rows.append(row)
smoothed=[]
for i,row in enumerate(rows):
 put(row)
 for n in names:
  if n=='Trident' or 'Finger' in n:continue
  ref=row[n].to_quaternion();v=np.zeros(4)
  for k in range(-18,19):
   q=rows[min(len(rows)-1,max(0,i+k))][n].to_quaternion();q=-q if q.dot(ref)<0 else q;v+=np.array(q)*math.exp(-.5*(k/6)**2)
  rig.pose.bones[n].rotation_quaternion=Quaternion(v/np.linalg.norm(v))
 smoothed.append(snap())
rows=smoothed;duration=end/30
def peak(rows):
 points=[];dirs=[]
 for row in rows:
  put(row);M=armik.W(rig,'Trident');points.append(M@Vector((0,1.1,0)));dirs.append(M.to_3x3()@Vector((0,1,0)))
 v=np.diff(np.array(points),axis=0)*120;ds=(np.array(dirs)[:-1]+np.array(dirs)[1:])/2;good=ds[:,1]/np.linalg.norm(ds,axis=1)<-math.cos(math.radians(70));speed=np.linalg.norm(v,axis=1);i=int(np.argmax(np.where(good,speed,-1)))
 return (frames[i]+.125)/30,float(speed[i])
before,speed=peak(rows);delta=before-1.;print('BEFORE RETIME',before,speed,flush=True);assert abs(delta)<.15,(before,speed);warped=[]
for f in frames:
 t=f/30;st=t+delta*math.sin(math.pi*t/duration)/math.sin(math.pi/duration);fi=float(np.clip(st*120,0,len(rows)-1));i=int(fi);j=min(i+1,len(rows)-1);w=fi-i;row={}
 for n in names:
  q=rows[i][n].to_quaternion().slerp(rows[j][n].to_quaternion(),w);m=q.to_matrix().to_4x4();m.translation=rows[i][n].translation.lerp(rows[j][n].translation,w);row[n]=m
 warped.append(row)
assert abs(delta)*math.pi/duration/math.sin(math.pi/duration)<.8
rows=warped;groups=[g.name for g in body.vertex_groups];feet=np.array([sum(e.weight for e in v.groups if groups[e.group].endswith(('_Foot','_Toe0')))>.5 for v in body.data.vertices])
for i,row in enumerate(rows):
 put(row);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(body.matrix_world@x.co) for x in me.vertices]);ev.to_mesh_clear();mm=armik.W(rig,'B_Pelvis');mm.translation.z+=.001-float(v[feet,2].min());armik.set_world(rig,'B_Pelvis',mm);rows[i]=snap()
after,speed=peak(rows);print('MEASURED TIP PEAK',before,'->',after,'speed',speed,flush=True)
bpy.data.actions.remove(a);a=bpy.data.actions.new('Attack');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end;act(a);prev={}
for f,row in zip(frames,rows):
 for n,m in row.items():
  q=m.to_quaternion()
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
  if n=='B_Pelvis':pb.location=m.translation;pb.keyframe_insert('location',frame=float(f))
written={'Attack':duration};code=(P/'scripts/attack_cannibal.py').read_text();exec(code[code.index('FA=.6;UA=.5;'):code.index('act(None);bpy.ops.wm.save_as_mainfile')])
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_textured_uv.blend'))
(P/'work/lunge_polish.json').write_text(json.dumps({'torso_filter_sigma_s':.05,'peak_before_s':before,'peak_after_s':after,'tip_speed_m_s':speed,'impact_s':1.0,'duration_s':duration},indent=2)+'\n')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/quick_rig_probe.py'),run_name='__main__')
