"""Choose one axial roll from the real crescent edges and measure the fastest target-facing cutting beat."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/gated_master.blend'));r=bpy.data.objects['Rig'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;rest=r.data.bones['Axe'].matrix_local;vs=np.array([v.co[:] for v in ax.data.vertices]);ids=np.where((abs(vs[:,0])>.21)&(vs[:,2]>.8))[0];points=vs[ids];times=np.arange(0,50.001,.5)
a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];mats=[]
for f in times:
 sc.frame_set(int(f),subframe=float(f%1));mats.append(np.array(r.pose.bones['Axe'].matrix@rest.inverted()))
mats=np.array(mats);rows=[]
for deg in range(0,180,5):
 rot=np.array(Matrix.Rotation(math.radians(deg),4,'Z'));mm=mats@rot;pts=np.einsum('tij,vj->tvi',mm[:,:3,:3],points)+mm[:,:3,3,None].transpose(0,2,1);vel=np.gradient(pts,1/60,axis=0);speed=np.linalg.norm(vel,axis=2);face=-mm[:,1,2];mask=(face>.5)&(times>2)&(times<48);sp=speed.copy();sp[~mask]=0;fi,vi=np.unravel_index(sp.argmax(),sp.shape);v=vel[fi,vi];n=mm[fi,:3,1];edge=mm[fi,:3,0]*np.sign(points[vi,0]);lead=float(v@edge/np.linalg.norm(v));flat=float(abs(v@n)/np.linalg.norm(v));rows.append({'roll_degrees':deg,'impact_seconds':float(times[fi]/30),'speed_m_s':float(sp[fi,vi]),'edge_leading_share':lead,'flat_normal_share':flat,'target_alignment':float(face[fi]),'mesh_vertex':int(ids[vi])})
best=max(rows,key=lambda v:v['edge_leading_share']-.1*v['flat_normal_share']);best['pass']=best['edge_leading_share']>.65 and best['flat_normal_share']<.40;print('BLADE',best,flush=True);assert best['pass'],best
angle=math.radians(best['roll_degrees'])
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget','Dead']:
 a=bpy.data.actions[name];poses=[];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);m=r.pose.bones['Axe'].matrix@rest.inverted();u=min(1,max(0,(f-5)/20));u=u*u*(3-2*u);roll=0 if name=='Dead' else angle*(1-u) if name=='Death' else angle;poses.append(m@Matrix.Rotation(roll,4,'Z')@rest)
 previous=None
 for f,m in enumerate(poses):
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(f);r.animation_data.action=None;r.pose.bones['Axe'].matrix=m;bpy.context.view_layer.update();pb=r.pose.bones['Axe'];q=pb.rotation_quaternion.copy()
  if previous is not None and q.dot(previous)<0:q=-q
  pb.rotation_quaternion=q;previous=q;r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
(P/'review/blade_gate.json').write_text(json.dumps({'selected':best,'sweep':rows,'method':'Actual crescent-edge vertices at 60 Hz; fastest tip while shaft points at target. Signed cutting edge lead, including both native axe bits.'},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gated_master.blend'))
