"""Transfer the protected near hand's skin weights to coarse left-hand vertices."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.reset();body=bpy.data.objects['Body'];me=body.data;me.calc_loop_triangles();names=[g.name for g in body.vertex_groups];co=[v.co.copy()for v in me.vertices];weights=[{names[g.group]:g.weight for g in v.groups if names[g.group].startswith(('B_','Cloth'))}for v in me.vertices];hand=np.array([sum(w for n,w in row.items()if n.startswith(('B_L_Hand','B_L_Finger')))>.2 for row in weights]);tri=[list(t.vertices)for t in me.loop_triangles if hand[list(t.vertices)].all()];tree=BVHTree.FromPolygons(co,tri,all_triangles=True);report=[]
for level in [1,2,3]:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));C.reset();body=bpy.data.objects['Body'];changed=[]
 for vertex in body.data.vertices:
  groups={body.vertex_groups[g.group].name:g.weight for g in vertex.groups};strength=sum(w for n,w in groups.items()if n.startswith(('B_L_Hand','B_L_Finger')))
  if strength<=.3:continue
  point,normal,face,distance=tree.find_nearest(vertex.co)
  if face is None or distance>.020:continue
  ids=tri[face];bary=np.array(barycentric_transform(point,*[co[i]for i in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))));bary=np.maximum(bary,0);bary/=bary.sum();new={}
  for i,a in zip(ids,bary):
   for n,w in weights[i].items():new[n]=new.get(n,0)+a*w
  new=sorted(new.items(),key=lambda x:-x[1])[:8];total=sum(w for n,w in new)
  for group in list(vertex.groups):body.vertex_groups[group.group].remove([vertex.index])
  for n,w in new:body.vertex_groups[n].add([vertex.index],w/total,'REPLACE')
  changed.append({'vertex':vertex.index,'projection_distance_mm':distance*1000})
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));report.append({'level':level,'vertices':changed});print('HAND_WEIGHT_TRANSFER',level,len(changed),flush=True)
(P/'review/round3_hand_weight_transfer.json').write_text(json.dumps(report,indent=2))
