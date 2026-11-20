import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_polished.blend'));F.r=bpy.data.objects['Rig'];F.body=bpy.data.objects['Body'];F.sc=bpy.context.scene;cache={n:[F.sample(bpy.data.actions[n],f) for f in range(int(bpy.data.actions[n].frame_range[1])+1)] for n in ['Attack','Cast']}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_clothed.blend'));r=bpy.data.objects['Rig'];F.r=r;F.body=bpy.data.objects['Body'];F.sc=bpy.context.scene
for n,rows in cache.items():
 bpy.data.actions.remove(bpy.data.actions[n]);a=bpy.data.actions.new(n);a.use_fake_user=True;prev={}
 for f,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for name in F.names:
   pb=r.pose.bones[name];q=pb.matrix_basis.to_quaternion()
   if name in prev and q.dot(prev[name])<0:q.negate()
   prev[name]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f*1.25);pb.keyframe_insert('location',frame=f*1.25)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=(len(rows)-1)*1.25
for role in ['Walking','Running']:
 a=bpy.data.actions[role];rows=[]
 for f in range(int(a.frame_range[1])+1):
  F.apply(F.sample(a,f));feet={s:F.M(f'B_{s}_Foot') for s in 'RL'};height=max(float(F.coords()[F.sole[s],2].min()) for s in 'RL');pel=F.M('B_Pelvis');pel.translation.z+=.025*max(0,min(1,(height-.01)/.08));F.setmat('B_Pelvis',pel)
  for s in 'RL':F.leg(s,feet[s].translation,feet[s].to_3x3())
  rows.append(F.snapshot())
 for f,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for name in ['B_Pelvis']+[f'B_{s}_{n}' for s in 'RL' for n in ['Thigh','Calf','Foot']]:
   pb=r.pose.bones[name];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
for a in bpy.data.actions:
 for lay in a.layers:
  for st in lay.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_timed.blend'))
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__',init_globals={'INPUT':'work/round1_timed.blend'})
sys.argv=['g','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_motion_trace.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_blade_audit.py'),run_name='__main__')
