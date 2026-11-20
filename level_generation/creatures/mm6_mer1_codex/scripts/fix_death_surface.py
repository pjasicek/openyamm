"""Correct the forward fall using signed boot-surface contact on both the near and coarse garment."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from surface_volumes import closed_faces,inside
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'));r=bpy.data.objects['Rig'];s=bpy.context.scene;body=bpy.data.objects['Body']
with bpy.data.libraries.load(str(P/'work/reduction/body_lod1_17_final.blend'),link=False)as(src,dst):dst.objects=['Body']
low=dst.objects[0];s.collection.objects.link(low);low.name='Coarse contact probe';low.parent=r
for mod in low.modifiers:
 if mod.type=='ARMATURE':mod.object=r
models=[]
for o in [body,low]:
 m=o.data;part=np.array([x.value for x in m.attributes['piece'].data]);faces=[tuple(f.vertices)for f in m.polygons];rest=np.array([v.co[:]for v in m.vertices]);cf=np.array([f for f in faces if len(f)==3 and part[f[0]]==2 and rest[list(f),2].min()>.335],dtype=int);parts=closed_faces(m,part,faces);gn={g.index:g.name for g in o.vertex_groups};models.append((o,part,cf,parts,gn))
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];report=[]
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 s.frame_set(int(f),subframe=float(f%1));largest=0.
 for iteration in range(28):
  worst=None
  for o,part,cf,parts,gn in models:
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear()
   tri=co[cf];samples=np.concatenate([tri[:,0],tri[:,1],tri[:,2],tri.mean(1),(tri[:,0]+tri[:,1])*.5,(tri[:,1]+tri[:,2])*.5,(tri[:,2]+tri[:,0])*.5]);samplefaces=np.tile(np.arange(len(cf)),7)
   for pid in [6,7]:
    boot=co[part==pid];tree=BVHTree.FromPolygons(co.tolist(),parts[pid][0]);use=np.where(np.all((samples>=boot.min(0))&(samples<=boot.max(0)),axis=1))[0]
    for si in use:
     point=Vector(samples[si]);loc,n,fi,d=tree.find_nearest(point)
     if loc is None or d<.0007 or not parts[pid][1][fi]or(point-loc).dot(n)>=0 or not inside(point,tree):continue
     if worst is None or d>worst[0]:worst=(d,point,loc+(loc-point).normalized()*.006,o,cf[samplefaces[si]],gn)
   for vi in np.where((part==2)&(co[:,2]<.001))[0]:
    d=.001-co[vi,2]
    if d>.0007 and(worst is None or d>worst[0]):point=Vector(co[vi]);worst=(d,point,point+Vector((0,0,d+.003)),o,[vi],gn)
  if worst is None:break
  d,point,target,o,ids,gn=worst;largest=max(largest,d);chains={}
  for vi in ids:
   for g in o.data.vertices[vi].groups:
    name=gn[g.group]
    if name.startswith('Cloak_'):
     c=int(name.split('_')[1]);chains[c]=chains.get(c,0)+g.weight
  assert chains
  c=max(chains,key=chains.get)
  for chain,share in [(c,1),((c-1)%16,.5),((c+1)%16,.5)]:
   pb=r.pose.bones[f'Cloak_{chain}_0'];M=pb.matrix.copy();M.translation+=(target-point)*share*1.25;pb.matrix=M;bpy.context.view_layer.update()

 for pb in r.pose.bones:
  if pb.name.startswith('Cloak_'):pb.keyframe_insert('rotation_quaternion',frame=float(f));pb.keyframe_insert('location',frame=float(f))
 report.append({'time':float(f/30),'iterations':iteration,'correction_max_m':largest})
for l in a.layers:
 for st in l.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    if 'Cloak_'in fc.data_path:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
# Keep quaternion signs continuous; pose rotations can choose equivalent opposite signs.
groups={}
for l in a.layers:
 for st in l.strips:
  for cb in st.channelbags:
   for fc in cb.fcurves:
    if 'Cloak_'in fc.data_path and fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
for group in groups.values():
 previous=None
 for i in range(len(group[0].keyframe_points)):
  q=np.array([group[j].keyframe_points[i].co.y for j in range(4)])
  if previous is not None and q@previous<0:
   q=-q
   for j in range(4):group[j].keyframe_points[i].co.y=q[j]
  previous=q
 for fc in group.values():fc.update()
bpy.data.objects.remove(low,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduction_master.blend'));(P/'review/death_surface_correction.json').write_text(json.dumps(report,indent=2));print('DEATH SURFACE CORRECTION',max(x['correction_max_m']for x in report),flush=True)
