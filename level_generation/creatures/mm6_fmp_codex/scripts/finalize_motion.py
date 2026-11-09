import bpy,sys,runpy,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_twist.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];s=bpy.context.scene
pieces=np.array([v.value for v in body.data.attributes['piece'].data]);feet=np.where(np.isin(pieces,[5,6]))[0]
def use(a):
 rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
def points():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return co
use(bpy.data.actions['Run']);floors=[];roots=[]
for f in range(25):
 s.frame_set(f);floors.append(float(points()[feet,2].min()));roots.append(rig.pose.bones['B_Pelvis'].location.copy())
lift=.008-min(floors);axis=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()@Vector((0,0,lift))
for f,loc in enumerate(roots):
 rig.pose.bones['B_Pelvis'].location=loc+axis;rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=f)
print('RUN ground correction',lift,'previous foot range',min(floors),max(floors),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_grounded.blend'))
sys.argv=['skirt_sim.py','--',str(p/'work/motion_grounded.blend'),str(p/'work/motion_grounded_cloth.blend'),'Run']
runpy.run_path(str(p/'scripts/skirt_sim.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];s=bpy.context.scene;allrows={}
for name in ('Standing','Walking','Run','Hit','Fidget','Death'):
 a=bpy.data.actions[name];use(a);end=float(a.frame_range[1]);n=45 if name in ('Hit','Fidget') else round(end*2);rows=[]
 for f in range(n+1):
  at=end*f/n;s.frame_set(math.floor(at),subframe=at%1);rows.append({b.name:(b.location.copy(),b.rotation_quaternion.copy()) for b in rig.pose.bones})
 allrows[name]=rows
allrows['Dead']=[allrows['Death'][-1] for _ in range(61)]
rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
s.render.fps=60;s.render.fps_base=1
for name,rows in allrows.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;use(a);last={}
 for f,row in enumerate(rows):
  for n,(loc,q) in row.items():
   q=q.copy()
   if n in last and last[n].dot(q)<0:q.negate()
   last[n]=q.copy();b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=loc;b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
assert len(rig.data.bones)==90
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_final.blend'))
# Dense edge/floor audit, including in-between export samples and rigid ordinary hands.
me=body.data;rest=np.array([v.co[:] for v in me.vertices]);edges=np.array([e.vertices[:] for e in me.edges]);L=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);piece=np.array([v.value for v in me.attributes['piece'].data]);reports={}
for name in allrows:
 use(bpy.data.actions[name]);end=int(bpy.data.actions[name].frame_range[1]);maxratio=np.ones(len(edges));floor=1e6;endpoint=[]
 for f in np.arange(0,end+.01,.5):
  s.frame_set(int(f),subframe=f%1);co=points();assert np.isfinite(co).all();floor=min(floor,float(co[:,2].min()));ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(L,1e-6);maxratio=np.maximum(maxratio,ratio)
  if f in (0,end):endpoint.append(co)
 info={'samples':end*2+1,'floor_m':floor,'parts':{}}
 for part in (0,1,2,3,7):
  mask=(piece[edges[:,0]]==part)&(piece[edges[:,1]]==part)&(L>.0001);r=maxratio[mask];info['parts'][part]={'p99':float(np.percentile(r,99)),'max':float(r.max())}
  if part in (2,3):assert r.max()<1.001,(name,part,r.max())
 info['loop_delta_m']=float(np.linalg.norm(endpoint[-1]-endpoint[0],axis=1).max());reports[name]=info
(p/'work/deformation_gate.json').write_text(json.dumps(reports,indent=2));print('DEFORMATION',json.dumps(reports),flush=True)
