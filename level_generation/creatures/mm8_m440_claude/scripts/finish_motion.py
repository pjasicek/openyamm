"""Keep the impact and low recoil, then return to guard within the fastest native recovery."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_grip.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
parts=np.array([a.value for a in body.data.attributes['piece'].data]);feet=np.flatnonzero(np.isin(parts,[4,5]))
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snapshot(a,f):
 act(a);sc.frame_set(f);return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def restore(snap):
 act(None)
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def mix(a,b,w):
 out={}
 for n in a:
  q=a[n].to_quaternion();r=b[n].to_quaternion()
  if q.dot(r)<0:r=-r
  m=q.slerp(r,w).to_matrix().to_4x4();m.translation=a[n].translation.lerp(b[n].translation,w);out[n]=m
 return out
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def ground(name):
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear()
 low=float(co[:,2].min() if name=='Death' else co[feet,2].min());dz=.002-low
 if name=='Running':dz=max(0,dz)
 M=armik.W(rig,'B_Pelvis');M.translation.z+=dz;armik.set_world(rig,'B_Pelvis',M)
def write(name,frames):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;act(a);prev={}
 for f,snap in enumerate(frames):
  for n,m in snap.items():
   b=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(frames)-1
st=snapshot(bpy.data.actions['Standing'],0);report={}
for name in ('Attack','Hit','Fidget','Death','Running'):
 a=bpy.data.actions[name];N=41 if name=='Attack' else int(a.frame_range[1]);raw=[snapshot(a,f) for f in range(N+1)];frames=[]
 for f,snap in enumerate(raw):
  if name=='Attack' and f>29:snap=mix(snap,st,smooth((f-29)/(N-29)))
  elif name in ('Hit','Fidget','Death'):
   w=smooth(f/(4 if name=='Hit' else 6))
   if name!='Death':w=min(w,smooth((N-f)/(5 if name=='Hit' else 8)))
   snap=mix(st,snap,w)
  restore(snap)
  for side in 'LR':rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
  ground(name);frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 if name=='Running':frames[-1]=frames[0]
 write(name,frames);report[name]={'frames':N+1,'duration':N/30}
 if name=='Death':write('Dead',[frames[-1],frames[-1]])
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_timed.blend'))
report['attack_timing']={'impact':26/30,'native_impact':1.,'end':41/30,'native_recovery_seconds':[110/60,100/60,90/60],'presented_end':1+(41-26)/30,'preserved_source_frames':[0,29],'recovery_blend_frames':[30,41]}
(p/'work/motion_timing.json').write_text(json.dumps(report,indent=2));print('TIMING',report)
