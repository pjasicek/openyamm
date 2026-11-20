import bpy,json,sys,math,numpy as np,shutil
from pathlib import Path
from mathutils import Quaternion,Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));backup=P/'work/review1/pre_polish.blend'
if not backup.exists():shutil.copyfile(P/'work/reduction_master.blend',backup)
# Reuse the existing fitted-source elbow solver; only apply it to the new library run.
code=(P/'scripts/fit_motion.py').read_text().split("roles=['Standing'")[0].replace("P/'work/actions_geometry_v2.blend'", "P/'work/review1/pre_polish.blend'")
exec(compile(code,str(P/'scripts/fit_motion.py'),'exec'))
report={};a=bpy.data.actions['Running'];act(a);fs=np.arange(0,24.0001,.25);poses=[]
for f in fs:
 scene.frame_set(int(f),subframe=float(f%1));before=capture();poses.append((float(f),before))
for f,pose in poses:
 apply(pose)
 for sd in 'LR':elbow(sd)
 fixed={n:rig.pose.bones[n].matrix_basis.copy()for n in [f'B_{sd}_{part}'for sd in 'LR'for part in ['Forearm','Hand']]};act(a)
 for n,M in fixed.items():
  b=rig.pose.bones[n];b.matrix_basis=M;b.keyframe_insert('rotation_quaternion',frame=f)
# Remove every old cloth key before resampling: subframe collision keys must not survive between smoothed samples.
for role,sigma in [('Death',.16),('Running',.075),('Walking',.075)]:
 a=bpy.data.actions[role];act(a);fs=np.arange(0,float(a.frame_range[1])+.001,.25);names=[n for n in rig.pose.bones.keys()if n.startswith('Cloak_')];data={n:[]for n in names}
 for f in fs:
  scene.frame_set(int(f),subframe=float(f%1))
  for n in names:
   b=rig.pose.bones[n];q=b.rotation_quaternion.copy()
   if data[n]and q.dot(Quaternion(data[n][-1][:4]))<0:q=-q
   data[n].append([*q,*b.location])
 removed=0;offgrid=0
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in list(cb.fcurves):
     if 'Cloak_'in fc.data_path:
      offgrid+=sum(abs(k.co.x*4-round(k.co.x*4))>1e-4 for k in fc.keyframe_points);cb.fcurves.remove(fc);removed+=1
 for n,values in data.items():
  arr=np.array(values)
  for f in fs:
   delta=fs-f
   if role!='Death':delta=(delta+float(fs[-1])/2)%float(fs[-1])-float(fs[-1])/2
   weights=np.exp(-.5*(delta/(sigma*30))**2);weights[abs(delta)>sigma*90]=0;v=weights@arr/weights.sum();v[:4]/=np.linalg.norm(v[:4]);b=rig.pose.bones[n];b.rotation_quaternion=v[:4];b.location=v[4:];b.keyframe_insert('rotation_quaternion',frame=float(f));b.keyframe_insert('location',frame=float(f))
 report[role]={'sigma_s':sigma,'removed_old_channels':removed,'removed_off_grid_keys':offgrid,'bake_hz':120}
# Shift parked club 13 mm outward so its wood touches the cloth rather than sitting inside it.
for a in bpy.data.actions:
 if a.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 act(a)
 for f in np.arange(0,float(a.frame_range[1])+.001,.25):
  scene.frame_set(int(f),subframe=float(f%1));M=rig.pose.bones['Club'].matrix.copy();w=1
  if a.name=='Attack':w=1-smooth(f/6)*smooth((float(a.frame_range[1])-f)/7.5)
  delta=(rig.pose.bones['B_Pelvis'].matrix@rig.data.bones['B_Pelvis'].matrix_local.inverted()).to_3x3()@Vector((-.013*w,0,0));M.translation+=delta;rig.pose.bones['Club'].matrix=M;rig.pose.bones['Club'].keyframe_insert('location',frame=float(f))
act(bpy.data.actions['Death']);scene.frame_set(int(bpy.data.actions['Death'].frame_range[1]));terminal=capture();act(None);bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;act(a)
for f in [0,30]:
 for n,(q,l)in terminal.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    # Normalize quaternion signs after world-space IK keys.
    qs={}
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
     if fc.data_path.endswith('rotation_quaternion'):qs.setdefault(fc.data_path,{})[fc.array_index]=fc
    for cs in qs.values():
     if len(cs)!=4:continue
     prev=None
     for i in range(min(len(c.keyframe_points)for c in cs.values())):
      q=np.array([cs[j].keyframe_points[i].co.y for j in range(4)])
      if prev is not None and q@prev<0:
       q=-q
       for j in range(4):cs[j].keyframe_points[i].co.y=q[j]
      prev=q
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'))
sel=json.loads((P/'review/reduction/selection.json').read_text())
for entry in [{'blend':'work/reduction_master.blend'}]+sel['body']:
 path=P/entry['blend'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];r.animation_data.action=None
 if entry['blend']!='work/reduction_master.blend':
  for a in list(bpy.data.actions):bpy.data.actions.remove(a)
  with bpy.data.libraries.load(str(P/'work/reduction_master.blend'),link=False)as(src,dst):dst.actions=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
  for a in dst.actions:a.use_fake_user=True
 parts=[v.value for v in o.data.attributes['piece'].data]
 for v in o.data.vertices:
  pid=parts[v.index]
  if pid in [8,9] and v.co.z>1.16 and abs(v.co.x)<.38:
   t=smooth((abs(v.co.x)-.16)/.22);sd='R'if pid==8 else'L'
   for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
   for n,w in [('B_Spine2',1-t),(f'B_{sd}_UpperArm',t*.6),(f'B_{sd}_UpperArmTwist',t*.4)]:
    if w>1e-7:o.vertex_groups[n].add([v.index],w,'REPLACE')
  elif pid==12 and -.257<v.co.x<-.213 and .083<v.co.y<.127 and .900<v.co.z<.921:v.co.x-=.013
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
(P/'review/review1_polish.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
