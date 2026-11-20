"""Dense checks for the changed clips on the selected textured mesh."""
from pathlib import Path
import bpy,json,math,numpy as np
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_v2.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=24
me=body.data;rest=np.array([v.co[:] for v in me.vertices]);wing=np.array([x.value for x in me.attributes['wing'].data],bool);me.calc_loop_triangles()
wtri=[list(t.vertices) for t in me.loop_triangles if wing[list(t.vertices)].all() and np.abs(rest[list(t.vertices),0]).min()>.12]
btri=[list(t.vertices) for t in me.loop_triangles if not wing[list(t.vertices)].any()]
assert len(wtri)>500 and len(btri)>1000
report={}
for name in ['Attack','Hit']:
 rig.animation_data.action=bpy.data.actions[name];end=float(rig.animation_data.action.frame_range[1]);floor=10.;collisions=[];sockets=[];heads=[];roots=[]
 for f in np.arange(0,end+.01,.25):
  sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();arr=np.array(co);assert np.isfinite(arr).all();floor=min(floor,float(arr[:,2].min()))
  if f%1==0:
   hits=BVHTree.FromPolygons(co,wtri,all_triangles=True).overlap(BVHTree.FromPolygons(co,btri,all_triangles=True))
   if hits:collisions.append({'time':f/24,'pairs':len(hits)})
  m=rig.pose.bones['Socket_Mouth'].head;sockets.append({'time':f/24,'horizontal':math.hypot(m.x,m.y)*1504.288787354,'small_z':m.z*1203.431029883})
  heads.append(list(rig.pose.bones['Head'].head));roots.append(list(rig.pose.bones['Root'].head))
 report[name]={'sample_rate':96,'samples':len(heads),'minimum_z':floor,'wing_body_collisions':collisions,'head_range':np.ptp(heads,axis=0).tolist(),'root_z_range':float(np.ptp(roots,axis=0)[2]),'max_socket_horizontal':max(x['horizontal'] for x in sockets),'max_small_socket_z':max(x['small_z'] for x in sockets)}
 if name=='Attack':assert max(x['horizontal'] for x in sockets)<600 and max(x['small_z'] for x in sockets)<450
(P/'review/motion_v2/dense_checks.json').write_text(json.dumps(report,indent=2)+'\n');print('DENSE',report,flush=True)
assert all(x['minimum_z']>=-0.0002 and not x['wing_body_collisions'] for x in report.values()),report
