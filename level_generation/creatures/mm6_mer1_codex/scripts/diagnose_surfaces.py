import bpy,bmesh,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/skirt_v1.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;pv=np.array([x.value for x in me.attributes['piece'].data]);faces=[tuple(f.vertices)for f in me.polygons]
for role,t,vi in [('Standing',2.895833,5883),('Standing',.5,5037),('Standing',.91666,2097),('Death',.3125,1697)]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];f=t*30;bpy.context.scene.frame_set(int(f),subframe=f%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy()for v in m.vertices];ev.to_mesh_clear();others=[fc for fc in faces if (pv[fc[0]]==2 if pv[vi]in[5,6,7]else pv[fc[0]]not in[pv[vi],4 if pv[vi]==8 else 3])];tree=BVHTree.FromPolygons(co,others);loc,n,fi,d=tree.find_nearest(co[vi]);print('POINT',role,t,vi,'part',pv[vi],'rest',tuple(me.vertices[vi].co),'POSE',tuple(co[vi]),'NEAR',tuple(loc),'N',tuple(n),'d',d,'signed',(co[vi]-loc).dot(n),'part',pv[others[fi][0]],'face',others[fi]);print('W',[(o.vertex_groups[e.group].name,e.weight)for e in me.vertices[vi].groups]);print('JOINTS',[(sd,k,tuple(r.pose.bones[f'B_{sd}_{k}'].head))for sd in'LR'for k in['UpperArm','Forearm','Hand']])
bm=bmesh.new();bm.from_mesh(me);layer=bm.verts.layers.int['piece'];seen=set()
for e in bm.edges:
 if not e.is_boundary or e in seen:continue
 stack=[e];es=[]
 while stack:
  q=stack.pop()
  if q in seen:continue
  seen.add(q);es.append(q)
  for v in q.verts:stack +=[a for a in v.link_edges if a.is_boundary and a not in seen]
 vs=set(v for a in es for v in a.verts);co=np.array([tuple(v.co)for v in vs]);print('BOUNDARY',len(vs),'parts',set(v[layer]for v in vs),'mean',co.mean(0),'lo',co.min(0),'hi',co.max(0))
