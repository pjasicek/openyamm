import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(ob.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return co
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_figc_authoring.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['FighterChain'];base=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);samples={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
 for f in sorted(set([0.,float(act.frame_range[1]),*[float(x) for x in np.arange(0,act.frame_range[1],5.625)]])):
  bpy.context.scene.frame_set(int(f),subframe=f%1);rows.append((f,coords(ob)))
 samples[act.name]=rows
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_figc_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');ob=next(o for o in bpy.data.objects if o.type=='MESH');rest=np.array([tuple(ob.matrix_world@v.co) for v in ob.data.vertices]);tree=kdtree.KDTree(len(base))
for i,p in enumerate(base):tree.insert(Vector(p),i)
tree.balance();mapping=[];worst=0
for p in rest:_,i,d=tree.find(Vector(p));mapping.append(i);worst=max(worst,d)
assert worst<.0001,worst
report={}
for name,rows in samples.items():
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];m=0;mf=0;keymax=0
 for f,reference in rows:
  bpy.context.scene.frame_set(int(f),subframe=f%1);diff=np.linalg.norm(coords(ob)-reference[mapping],axis=1);v=float(diff.max())
  if v>m:m,mf=v,f
  if f%1==0:keymax=max(keymax,v)
 report[name]={'max_surface_error_mm':m*1000,'worst_frame':mf,'integer_frame_error_mm':keymax*1000};print('PARITY',name,report[name],flush=True)
assert max(v['integer_frame_error_mm'] for v in report.values())<.2
(P/'work/export_parity.json').write_text(json.dumps({'rest_correspondence_mm':worst*1000,'clips':report},indent=2))
# UV triangle integrity. Shared boundary texels are excluded from the raster-overlap count.
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_motion.blend'));me=bpy.data.objects['Body'].data;me.calc_loop_triangles();head=np.array([d.value for d in me.attributes['head'].data]);result={}
for layer,ishead in [('UVMap',False),('HeadUV',True)]:
 uv=me.uv_layers[layer].data;hits=np.zeros((512,512),np.uint8);degenerate=0;count=0
 for tri in me.loop_triangles:
  if bool(head[tri.polygon_index])!=ishead:continue
  a,b,c=np.array([tuple(uv[i].uv) for i in tri.loops])*512;den=np.cross(b-a,c-a);count+=1
  if abs(float(den))<1e-8:degenerate+=1;continue
  lo=np.maximum(np.floor(np.minimum(np.minimum(a,b),c)).astype(int),0);hi=np.minimum(np.ceil(np.maximum(np.maximum(a,b),c)).astype(int),511)
  if (hi<lo).any():continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);v=np.stack([xx-a[0],yy-a[1]],-1);w1=(v[:,:,0]*(c-a)[1]-v[:,:,1]*(c-a)[0])/den;w2=((b-a)[0]*v[:,:,1]-(b-a)[1]*v[:,:,0])/den;m=(w1>1e-4)&(w2>1e-4)&(w1+w2<.9999);hits[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=m
 result[layer]={'triangles':count,'degenerate':degenerate,'covered_texels':int((hits>0).sum()),'overlap_texels':int((hits>1).sum()),'overlap_fraction':float((hits>1).sum()/max((hits>0).sum(),1))}
 print('UV_CHECK',layer,result[layer],flush=True)
 assert degenerate==0 and result[layer]['overlap_fraction']<.005
(P/'work/uv_checks.json').write_text(json.dumps(result,indent=2))
