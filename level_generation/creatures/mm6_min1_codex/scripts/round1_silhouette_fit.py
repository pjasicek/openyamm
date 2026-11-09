import bpy,sys,runpy,json,math,subprocess
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render'];R=P/'review/round1/reduction'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/L3_outline_fit_10.blend'));r=bpy.data.objects['Rig'];objects=[bpy.data.objects['Body'],bpy.data.objects['AxeMesh']];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);report=[]
for iteration in range(1,11):
 xyz=[];faces=[];ranges=[]
 for obj in objects:
  offset=len(xyz);e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();xyz.extend([v.co.copy() for v in me.vertices]);faces.extend([tuple(i+offset for i in f.vertices) for f in me.polygons]);ranges.append((obj,offset,len(me.vertices)));e.to_mesh_clear()
 tree=BVHTree.FromPolygons(xyz,faces);adj={};normals=[]
 for fi,f in enumerate(faces):
  normals.append((xyz[f[1]]-xyz[f[0]]).cross(xyz[f[2]]-xyz[f[0]]).normalized())
  for i,j in zip(f,f[1:]+f[:1]):adj.setdefault(tuple(sorted((i,j))),[]).append(fi)
 edges=[]
 for k in range(8):
  d=Vector((math.sin(k*math.pi/4),-math.cos(k*math.pi/4),0))
  for (i,j),ff in adj.items():
   if len(ff)==2 and normals[ff[0]].dot(d)*normals[ff[1]].dot(d)>0:continue
   mid=(xyz[i]+xyz[j])*.5;hit=tree.ray_cast(mid+d*6,-d)[0]
   if hit is not None and (hit-mid).length<.006:
    perp=d.cross(xyz[j]-xyz[i]).normalized();left=tree.ray_cast(mid+d*6+perp*.003,-d)[0];right=tree.ray_cast(mid+d*6-perp*.003,-d)[0]
    if (left is None)!=(right is None):edges.append((k,i,j))
 path=P/'work/reduction/silhouette/solve.json';path.parent.mkdir(exist_ok=True);path.write_text(json.dumps({'positions':[list(v) for v in xyz],'edges':edges}));subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_silhouette_solver.py'),str(path)],check=True);delta=json.loads(path.with_suffix('.delta.json').read_text())
 for obj,offset,count in ranges:
  matrices={g.index:r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted() for g in obj.vertex_groups if g.name in r.pose.bones}
  for v in obj.data.vertices:
   S=Matrix(((0,0,0,0),)*4)
   for g in v.groups:
    if g.group in matrices:S+=matrices[g.group]*g.weight
   v.co+=S.to_3x3().inverted_safe()@Vector(delta[offset+v.index])
  obj.data.update()
 bpy.context.view_layer.update()
 if iteration in [1,3,6,10]:
  dest=P/f'work/reduction/L3_subpixel_fit_{iteration}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'L3_subpixel_fit_{iteration}';render(folder,'Combined',3,directory=P/'textures/round1_rebaked')
  subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/'L3_combined_reference'),str(folder),str(folder/'metrics.json')],check=True);v=json.loads((folder/'metrics.json').read_text());report.append({'level':3,'iteration':iteration,'blend':str(dest.relative_to(P)),'pooled_iou':v['pooled_iou'],'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97});(R/'subpixel_fit.json').write_text(json.dumps(report,indent=2));print('OUTLINE RESULT',report[-1],flush=True)
