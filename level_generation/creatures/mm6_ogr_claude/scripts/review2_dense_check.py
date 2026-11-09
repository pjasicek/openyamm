"""Validate the fitted cloth/head at display subframes and record the native-height calibration."""
from pathlib import Path
import bpy,sys,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene;pv=me.attributes['piece'];clear=Clearance(body)
skin=[tuple(f.vertices) for f in me.polygons if all(pv.data[i].value==0 for i in f.vertices)];cloth=[f for f in me.polygons if pv.data[f.vertices[0]].value in [14,19]];report={}
for name in ['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=(0,None);hmax=0
 for f in np.unique(np.r_[np.arange(0,float(a.frame_range[1]),30/48),float(a.frame_range[1])]):
  sc.frame_set(int(f),subframe=float(f)%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,skin);hmax=max(hmax,clear.measure()[0])
  if name=='Standing' and f==0:
   lo=min(v.z for v in co);hi=max(v.z for v in co);height={'height_m':hi-lo,'bottom_m':lo,'top_m':hi,'native_world_height':248*.799988,'runtime_scale':248*.799988/(hi-lo)}
  for face in cloth:
   pts=[co[i] for i in face.vertices];pts.append(sum(pts,Vector())/len(pts))
   for v in pts:
    loc,n,fi,d=tree.find_nearest(v,.06)
    if loc is not None and d>worst[0] and (v-loc).dot(n)<-.707*d:worst=(d,float(f))
  
 report[name]={'cloth_depth_m':worst[0],'cloth_frame':worst[1],'head_depth_m':hmax};print('DENSE',name,report[name],flush=True)
 assert worst[0]<.003,(name,worst)
 assert hmax<.01,(name,hmax)
report['standing_calibration']=height;(p/'revision_02/motion/dense_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('CALIBRATION',height)
