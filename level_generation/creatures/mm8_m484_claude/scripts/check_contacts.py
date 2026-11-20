"""Half-frame surface contacts on the closed skin, separate mail and rigid axe."""
import os
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('CHECK_BLEND','work/pilots.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;me=b.data;rest=np.array([v.co[:] for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);ng=[g.name for g in b.vertex_groups];W=np.zeros((len(rest),len(ng)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
faces=[tuple(f.vertices) for f in me.polygons];skin=[f for f in faces if all(pv[i] in [0,1] for i in f)];cloth=[f for f in faces if all(pv[i]==100 and rest[i,2]<.86 for i in f)]
part={}
for sd in 'RL':
 arm=W[:,[i for i,n in enumerate(ng) if n.startswith(f'B_{sd}_') and any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]].sum(1);hand=W[:,[i for i,n in enumerate(ng) if n.startswith(f'B_{sd}_') and any(k in n for k in ['Forearm','Hand','Finger'])]].sum(1)
 part[sd]={'faces':[f for f in skin if all(arm[i]<.15 for i in f)],'ids':np.where(hand>.7)[0],'handfaces':[f for f in skin if all(hand[i]>.7 for i in f)]}
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();a=np.array([tuple(o.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear();return a
report={}
for nm in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];out={}
 for f in np.arange(0,a.frame_range[1]+.1,.5):
  sc.frame_set(int(f),subframe=f%1);co=coords(b);ap=coords(ax);tree=BVHTree.FromPolygons(co.tolist(),skin)
  checks=[('axe',tree,ap,np.arange(len(ap)))]
  pairs=BVHTree.FromPolygons(co.tolist(),cloth).overlap(tree);ci=sorted({v for i,j in pairs for v in cloth[i]});checks.append(('cloth',tree,co,ci))
  for sd,p in part.items():checks.append((sd+'_forearm_hand',BVHTree.FromPolygons(co.tolist(),p['faces']),co,p['ids']))
  for label,bvh,points,ids in checks:
   best=(0,None,None)
   for i in ids:
    loc,norm,fi,d=bvh.find_nearest(Vector(points[i]),.08)
    if loc is not None and d>best[0] and (Vector(points[i])-loc).dot(norm)<-.7*d:best=(d,int(i),int(fi))
   if best[0]>out.get(label,{}).get('depth_m',-1):out[label]={'depth_m':best[0],'frame':float(f),'vertex':best[1],'face':best[2]}
 report[nm]=out;print('CONTACTS',nm,out,flush=True)
(P/'review'/(os.environ.get('CHECK_PREFIX','pilot')+'_'+'contacts'+'.json')).write_text(json.dumps(report,indent=2))
