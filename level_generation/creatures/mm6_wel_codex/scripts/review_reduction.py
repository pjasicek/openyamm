import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
samples=[('Standing',1,'front'),('Standing',1,'left'),('Attack',39,'front'),('Attack',61,'front'),('Walking',22,'left')];source={};report={}
for label,file in [('before','anim_foam.blend'),('after','anim_uv.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/file));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
 for m in o.data.materials:m.diffuse_color=(.48,.53,.48,1)
 for ob in sc.objects:
  if ob.type=='MESH' and ob.name!='Body':ob.hide_render=True
 for clip,f,view in samples:
  r.animation_data.action=bpy.data.actions[clip];sc.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];ev.to_mesh_clear();key=f'{clip}_{f}_{view}'
  if label=='before':source[key]=(co,faces)
  else:
   c0,f0=source[key];b0=BVHTree.FromPolygons(c0,f0);b1=BVHTree.FromPolygons(co,faces);d=[b0.find_nearest(v)[3] for v in co]+[b1.find_nearest(v)[3] for v in c0];report[key]={'surface_error_m_p95_max':np.percentile(d,[95,100]).tolist()};assert max(d)<.025,(key,max(d))
  common.workbench_clay(sc);common.render_views(str(P/'review'/f'reduction_{label}_{clip}_{f}'),1.1,2.55,views=(view,),resolution=(500,600),target=(0,.30))
(P/'review/reduction_comparison.json').write_text(json.dumps(report,indent=2));print(report)
