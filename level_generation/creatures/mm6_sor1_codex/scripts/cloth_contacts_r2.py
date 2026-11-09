"""Correct baked robe bones against evaluated closed shoes and the floor, preserving mesh/UVs."""
import bpy, json, numpy as np, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def gaussian_filter1d(a,sigma,axis,mode):
 weights=np.exp(-np.arange(-2,3,dtype=float)**2/(2*sigma*sigma));weights/=weights.sum()
 padded=np.pad(a,((2,2),(0,0),(0,0)),mode='wrap' if mode=='wrap' else 'edge')
 return sum(w*padded[i:i+len(a)] for i,w in enumerate(weights))
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round2_gait.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene

pv=np.array([v.value for v in me.attributes['piece'].data]);ci=np.where(pv==100)[0]
shoe_faces=[tuple(f.vertices) for f in me.polygons if all(pv[i] in [101,102,103,104] for i in f.vertices)]
bones=[b.name for b in rig.data.bones if b.name.startswith('Robe_')];idx={n:i for i,n in enumerate(bones)}
W=np.zeros((len(ci),len(bones)))
for j,i in enumerate(ci):
 for g in me.vertices[int(i)].groups:
  n=body.vertex_groups[g.group].name
  if n in idx:W[j,idx[n]]=g.weight
# Unconnected cloth helper joints allow small baked corrections between the coarse chain samples.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n in bones:rig.data.edit_bones[n].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
regular=.15*np.eye(len(bones))+.03*W.T@W
scene.render.fps=120
report={}
def evaluate():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([x.co[:] for x in m.vertices]);ev.to_mesh_clear();return v
for role in ['Walking','Death']:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 frames=list(range(int(act.frame_range[0]),int(act.frame_range[1])+1));raw=[];baseline=[];centres=[];directions=[];cor=np.zeros((len(frames),len(bones),3))
 for f in frames:
  scene.frame_set(f);raw.append([rig.pose.bones[n].matrix.copy() for n in bones]);baseline.append(evaluate())
  centre=np.array(rig.pose.bones['B_Pelvis'].head);centre[1]-=.02;centres.append(centre)
  ds=[]
  for n in bones:
   angle=np.radians(-180+int(n.split('_')[1])*22.5);ds.append([np.sin(angle),np.cos(angle),0.])
  directions.append(np.array(ds))
 for iteration in range(40):
  worst=0
  for fi,f in enumerate(frames):
   v=baseline[fi].copy();v[ci]+=W@cor[fi];tree=BVHTree.FromPolygons(v.tolist(),shoe_faces);rows=[];targets=[]
   for j,i in enumerate(ci):
    x=Vector(v[i]);delta=Vector((0,0,0))
    if role=='Death':
     q,n,face,d=tree.find_nearest(x,.08)
     if q is not None and (x-q).dot(n)<.009:delta=n*(.012-(x-q).dot(n))
    else:
     q,n,face,d=tree.find_nearest(x,.15)
     if q is not None and (x-q).dot(n)<.012:
      d=Vector((x.x-centres[fi][0],x.y-centres[fi][1],0)).normalized()
      hit,_,_,_=tree.ray_cast(Vector((centres[fi][0],centres[fi][1],x.z))+d*1.5,-d,3)
      if hit is not None:delta=d*max(0.,(hit-x).dot(d)+.016)
    if x.z+delta.z<.012:delta.z=.012-x.z
    if delta.length>1e-5:rows.append(j);targets.append(list(delta));worst=max(worst,delta.length)
   if rows:
    A=W[rows];rhs=np.array(targets);change=np.linalg.solve(A.T@A+regular,A.T@rhs)
    if role in ['Walking','Attack']:
     ds=directions[fi];out=np.maximum(np.sum(change*ds,axis=1),0)
     change[:,:2]=ds[:,:2]*out[:,None];change[:,2]=np.maximum(change[:,2],0)
    cor[fi]+=change
  if iteration<20:cor=gaussian_filter1d(cor,1.2,axis=0,mode='wrap' if role in ['Standing','Walking'] else 'nearest')
  print('CONTACT',role,iteration,'correction mm',round(worst*1000,3),flush=True)
  if worst<.0003:break
 if role in ['Standing','Walking']:cor[-1]=cor[0]
 for fi,f in enumerate(frames):
  scene.frame_set(f)
  for j,n in enumerate(bones):
   M=raw[fi][j].copy();M.translation+=Vector(cor[fi,j]);pb=rig.pose.bones[n];pb.matrix=M;bpy.context.view_layer.update();pb.keyframe_insert('location',frame=f,group=n)
 for fi,f in enumerate(frames):
  scene.frame_set(f);v=evaluate();expected=baseline[fi].copy();expected[ci]+=W@cor[fi]
  error=np.linalg.norm(v-expected,axis=1).max()
  assert error<.0001,(role,f,'correction bake mismatch',float(error))
 report[role]={'max_bone_translation_mm':float(np.linalg.norm(cor,axis=2).max()*1000),'correction_acceleration_p99_mm':float(np.percentile(np.linalg.norm(np.diff(cor,n=2,axis=0),axis=2),99)*1000)}
(p/'work/round2_cloth_contacts.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round2_contacts.blend'))
