"""Accepted-motion invariance, grip alignment and signed garment poke checks at 48 Hz."""
import bpy,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/round3';roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
def scan(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in ob.vertex_groups];faces=[tuple(f.vertices) for f in me.polygons]
 weight=lambda keys:np.array([sum(g.weight for g in v.groups if any(k in names[g.group] for k in keys)) for v in me.vertices])
 img=bpy.data.images.load(str(P/'textures/figc_region_mask.png'),check_existing=True);img.colorspace_settings.name='Non-Color';pixels=np.array(img.pixels[:]).reshape(img.size[1],img.size[0],4);uv=me.uv_layers['UVMap'].data;cloth=[]
 for f in me.polygons:
  if not np.all(pv[list(f.vertices)]==0):continue
  z=co[list(f.vertices),2].mean()
  if not .55<z<1.02:continue
  v=sum((uv[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices);x=int(np.clip(v.x*img.size[0],0,img.size[0]-1));y=int(np.clip(v.y*img.size[1],0,img.size[1]-1))
  if pixels[y,x,:2].sum()>.5:cloth.append(tuple(f.vertices))
 cloth_ids={i for f in cloth for i in f};legs=np.where((weight(['Thigh','Calf','Foot','Toe'])>.3)&~np.isin(np.arange(len(co)),list(cloth_ids)))[0]
 groups={'skirt':(cloth,legs)}
 for side,pieces,hand in [('L',[4],1),('R',[5,12],2)]:groups[side+'_sleeve']=([f for f in faces if np.isin(pv[list(f)],pieces).all()],np.where(pv==hand)[0])
 def signed(C,fs,ids):
  tree=BVHTree.FromPolygons([Vector(c) for c in C],fs);out={}
  for i in ids:
   p=Vector(C[i]);loc,n,fi,d=tree.find_nearest(p,.05)
   if loc is not None:out[int(i)]=((p-loc).dot(n)>.707*d and d>1e-6,float(d)*1000)
  return out
 rest={k:signed(co,*v) for k,v in groups.items()};poses={};report={}
 for role in roles:
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];samples=[];row={k:0.0 for k in groups};row['frames']=0
  for f in np.arange(0,float(a.frame_range[1])+.001,.625):
   bpy.context.scene.frame_set(int(f),subframe=float(f%1));samples.append(np.array([tuple(x) for b in rig.pose.bones for x in b.matrix],dtype=np.float32));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();C=[ob.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
   for k,(fs,ids) in groups.items():
    for i,(outside,d) in signed(C,fs,ids).items():
     if outside and i in rest[k] and not rest[k][i][0]:row[k]=max(row[k],d)
   row['frames']+=1
  poses[role]=np.array(samples);report[role]=row
 return poses,report
baseline,old=scan(R/'before/work/export_validation.blend');result={'method':'All bone matrices vs accepted export; signed garment poke follows the humanoid playbook: outside within a 45-degree face-normal cone, previously inside at rest, nearest face within 50 mm.','baseline_cloth_mm':old,'lods':{}}
for level in range(4):
 path=P/'work/export_validation.blend' if level==0 else R/f'validation_lod{level}/export_validation.blend';poses,cloth=scan(path);rows={}
 for role in roles:
  delta=float(np.max(np.abs(poses[role]-baseline[role])));rows[role]={'bone_matrix_max_abs_delta':delta,'elbow_roll_palm_unchanged':delta<1e-6,'cloth_mm':cloth[role],'cloth_increase_mm':{k:cloth[role][k]-old[role][k] for k in ['skirt','L_sleeve','R_sleeve']}}
 result['lods'][str(level)]=rows;print('PRESERVATION',level,json.dumps(rows),flush=True)
(R/'gates/preservation.json').write_text(json.dumps(result,indent=2)+'\n')
