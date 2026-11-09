import bpy,runpy,sys,json,math,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render'];R=P/'review/round1/reduction'
def geometry(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);xyz=[];faces=[];norm=[];ranges=[]
 for obj in [bpy.data.objects['Body'],bpy.data.objects['AxeMesh']]:
  offset=len(xyz);e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();xyz.extend([v.co.copy() for v in me.vertices]);norm.extend([v.normal.copy() for v in me.vertices]);faces.extend([tuple(i+offset for i in f.vertices) for f in me.polygons]);ranges.append((obj,offset,len(me.vertices)));e.to_mesh_clear()
 return xyz,faces,norm,ranges
high,hf,_,_=geometry(P/'work/round1_high.blend');xyz,faces,norm,ranges=geometry(P/'work/reduction/L3_outline_fit_10.blend');r=bpy.data.objects['Rig'];tree=BVHTree.FromPolygons(xyz,faces);active=set();adj={};ns=[]
for fi,f in enumerate(faces):
 ns.append((xyz[f[1]]-xyz[f[0]]).cross(xyz[f[2]]-xyz[f[0]]).normalized())
 for i,j in zip(f,f[1:]+f[:1]):adj.setdefault(tuple(sorted((i,j))),[]).append(fi)
for k in range(8):
 d=Vector((math.sin(k*math.pi/4),-math.cos(k*math.pi/4),0))
 for (i,j),ff in adj.items():
  if len(ff)==2 and ns[ff[0]].dot(d)*ns[ff[1]].dot(d)>0:continue
  mid=(xyz[i]+xyz[j])*.5;perp=d.cross(xyz[j]-xyz[i]).normalized();l=tree.ray_cast(mid+d*6+perp*.004,-d)[0];rr=tree.ray_cast(mid+d*6-perp*.004,-d)[0]
  if (l is None)!=(rr is None):active.update([i,j])
path=P/'work/reduction/raster_fit.json';path.write_text(json.dumps({'low':[list(v) for v in xyz],'faces':faces,'normals':[list(v) for v in norm],'high':[list(v) for v in high],'high_faces':hf,'active':sorted(active),'diameter':2.689537525177002}));subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_raster_solver.py'),str(path)],check=True);result=json.loads(path.with_suffix('.result.json').read_text());delta=np.array(result['positions'])-np.array(xyz)
for obj,offset,count in ranges:
 matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted() for g in obj.vertex_groups if g.name in r.pose.bones}
 for v in obj.data.vertices:
  S=Matrix(((0,0,0,0),)*4)
  for g in v.groups:
   if g.group in matrices:S+=matrices[g.group]*g.weight
  v.co+=S.to_3x3().inverted_safe()@Vector(delta[offset+v.index])
 obj.data.update()
bpy.context.view_layer.update();dest=P/'work/reduction/L3_raster_fit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/'L3_raster_fit';render(folder,'Combined',3,directory=P/'textures/round1_rebaked');subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/'L3_runtime_reference'),str(folder),str(folder/'metrics.json')],check=True);v=json.loads((folder/'metrics.json').read_text());v['blend']=str(dest.relative_to(P));v['pass']=v['pooled_iou']>=.97;v['optimization']=result['history'];(R/'raster_fit.json').write_text(json.dumps(v,indent=2));print('RASTER FINAL',v['pooled_iou'],v['pass'],flush=True)
