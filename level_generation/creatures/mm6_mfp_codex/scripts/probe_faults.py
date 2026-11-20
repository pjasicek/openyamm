import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;co=np.array([v.co[:]for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);gn={g.index:g.name for g in b.vertex_groups};E=np.array([e.vertices[:]for e in me.edges]);rl=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);faces=[f.vertices[:]for f in me.polygons]
def weights(i):return sorted([(gn[g.group],round(g.weight,3))for g in me.vertices[i].groups],key=lambda x:-x[1])[:6]
for an,fr in [('Standing',0),('Walking',25),('Attack',15),('Death',40)]:
 a=bpy.data.actions[an];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(fr);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pos=np.array([v.co[:]for v in mm.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(pos[E[:,0]]-pos[E[:,1]],axis=1)/np.maximum(rl,1e-6)
 for sd in 'LR':
  arm=np.array([sum(g.weight for g in v.groups if gn[g.group].startswith(f'B_{sd}_')and any(w in gn[g.group]for w in ['UpperArm','Clavicle','Forearm','Hand','Finger']))for v in me.vertices]);hand=np.array([sum(g.weight for g in v.groups if gn[g.group].startswith(f'B_{sd}_')and any(w in gn[g.group]for w in ['Forearm','Hand','Finger']))>.5 for v in me.vertices]);mask=(arm[E[:,0]]>.3)&(arm[E[:,1]]>.3);ix=np.argmax(np.where(mask,ratio,0));print('EDGE',an,sd,'ratio',ratio[ix],[(int(i),int(pv[i]),co[i].tolist(),weights(i))for i in E[ix]])
  fl=[f for f in faces if all(arm[i]<.2 for i in f)];tr=BVHTree.FromPolygons(pos.tolist(),fl);worst=(0,None)
  for i in np.flatnonzero(hand):
   loc,n,idx,d=tr.find_nearest(Vector(pos[i]),.05)
   if loc is not None and d>worst[0]and(Vector(pos[i])-loc).dot(n)<-.7*d:worst=(d,(int(i),int(pv[i]),co[i].tolist(),weights(i),int(pv[fl[idx][0]]),[float(x)for x in pos[i]],[float(x)for x in loc]))
  print('CONTACT',an,sd,worst)
