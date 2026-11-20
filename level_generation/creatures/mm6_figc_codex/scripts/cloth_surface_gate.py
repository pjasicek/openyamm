"""Signed penetration only at confirmed triangle/wall crossings, excluding 5-mm opening rims."""
import bpy,json,math
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
P=Path(__file__).resolve().parents[1];R=P/'review/round3';ROLES=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
def scan(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;me.calc_loop_triangles();co=[v.co.copy() for v in me.vertices];pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in ob.vertex_groups];leg=np.array([sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['Thigh','Calf','Foot','Toe']))>.3 for v in me.vertices]);uv=me.uv_layers['UVMap'].data
 img=bpy.data.images.load(str(P/'textures/figc_region_mask.png'),check_existing=True);img.colorspace_settings.name='Non-Color';pix=np.array(img.pixels[:]).reshape(img.size[1],img.size[0],4);cloth=[]
 for f in me.polygons:
  if not all(pv[i]==0 for i in f.vertices) or not .55<sum(co[i].z for i in f.vertices)/len(f.vertices)<1.02:continue
  v=sum((uv[i].uv for i in f.loop_indices),Vector((0,0)))/len(f.loop_indices);x=int(np.clip(v.x*img.size[0],0,img.size[0]-1));y=int(np.clip(v.y*img.size[1],0,img.size[1]-1))
  if pix[y,x,:2].sum()>.5:cloth.append(f.index)
 groups={};tri=list(me.loop_triangles)
 for label,wall,skin in [('skirt',lambda t:t.polygon_index in cloth,lambda t:t.polygon_index not in cloth and leg[list(t.vertices)].all()),('L_sleeve',lambda t:np.isin(pv[list(t.vertices)],[4]).all(),lambda t:np.all(pv[list(t.vertices)]==1)),('R_sleeve',lambda t:np.isin(pv[list(t.vertices)],[5,12]).all(),lambda t:np.all(pv[list(t.vertices)]==2))]:
  walls=[tuple(t.vertices) for t in tri if wall(t)];skins=[tuple(t.vertices) for t in tri if skin(t)];counts=Counter();edge_ids={}
  for f in walls:
   for a,b in zip(f,f[1:]+f[:1]):
    key=tuple(sorted((tuple(round(x,6) for x in co[a]),tuple(round(x,6) for x in co[b]))));counts[key]+=1;edge_ids[key]=(a,b)
  boundary=[edge_ids[k] for k,v in counts.items() if v==1];groups[label]=(walls,skins,boundary)
 def crossing(A,B):
  for source,target in [(A,B),(B,A)]:
   for a,b in zip(source,source[1:]+source[:1]):
    v=b-a;length=v.length
    if length<1e-8:continue
    hit=intersect_ray_tri(*target,v.normalized(),a,True)
    if hit is not None and 1e-5<(hit-a).dot(v.normalized())<length-1e-5:return hit
  return None
 report={}
 for role in ROLES:
  act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];row={k:{'max_penetration_mm':0.0,'crossings':0,'worst_frame':None} for k in groups};row['frames']=0
  for frame in np.arange(0,float(act.frame_range[1])+.001,.625):
   bpy.context.scene.frame_set(int(frame),subframe=float(frame%1));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();C=[ob.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear()
   for label,(walls,skins,boundary) in groups.items():
    wt=BVHTree.FromPolygons(C,walls,all_triangles=True);st=BVHTree.FromPolygons(C,skins,all_triangles=True)
    for wi,si in wt.overlap(st):
     A=[C[i] for i in skins[si]];B=[C[i] for i in walls[wi]];hit=crossing(A,B)
     if hit is None:continue
     near=False
     for a,b in boundary:
      e=C[b]-C[a];t=max(0,min(1,(hit-C[a]).dot(e)/max(e.length_squared,1e-12)))
      if (hit-C[a]-e*t).length<.005:near=True;break
     if near:continue
     n=(B[1]-B[0]).cross(B[2]-B[0]).normalized();depth=max(0,max((v-B[0]).dot(n) for v in A))*1000;row[label]['crossings']+=1
     if depth>row[label]['max_penetration_mm']:row[label].update(max_penetration_mm=float(depth),worst_frame=float(frame))
   row['frames']+=1
  report[role]=row;print('CLOTH_SURFACE',path.parent.name,role,row,flush=True)
 return report
baseline=scan(R/'before/work/export_validation.blend');result={'method':__doc__,'baseline':baseline,'lods':{}}
for level in range(4):
 path=P/'work/export_validation.blend' if level==0 else R/f'validation_lod{level}/export_validation.blend';data=scan(path);result['lods'][str(level)]=data
(R/'gates/cloth_surface.json').write_text(json.dumps(result,indent=2)+'\n')
