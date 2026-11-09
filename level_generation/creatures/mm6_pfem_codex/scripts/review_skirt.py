import bpy,sys,numpy as np,json,runpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data;pv=np.array([a.value for a in me.attributes['piece'].data])
common.workbench_clay(bpy.context.scene)
for an,f in [('Standing',0),('Walking',6),('Walking',18),('Hit',14),('Death',30),('Death',45),('Death',60)]:
 a=bpy.data.actions[an];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f)
 common.render_views(str(p/f'review/skirt_{an}_{f}'),.84,1.85,views=('front','left','three_quarter'),resolution=(600,900))
 if an in ('Hit','Death'):
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();P=[v.co.copy() for v in mm.vertices];ev.to_mesh_clear()
  for part,target in [(3,4),(4,3),(9,1)]:
   fs=[tuple(f.vertices) for f in me.polygons if all(pv[i]==target for i in f.vertices)]
   tree=BVHTree.FromPolygons(P,fs);worst=(0,None)
   for i in np.flatnonzero(pv==part):
    loc,n,fi,d=tree.find_nearest(P[i],.05)
    if loc is not None and (P[i]-loc).dot(n)<-.7*d and d>worst[0]:worst=(d,{'part':part,'target':target,'vertex':int(i),'point':list(P[i]),'normal':list(n)})
   print('CONTACT',an,f,worst)
  common.render_views(str(p/f'review/contact_{an}_{f}'),.22 if an=='Death' else 1.07,.7,views=('front','left'),resolution=(700,700),target=(.14,-.22))
