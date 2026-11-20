import bpy,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene;pv=np.array([a.value for a in me.attributes['piece'].data]);sf=[tuple(f.vertices)for f in me.polygons if pv[f.vertices[0]]==2];pf=[tuple(f.vertices)for f in me.polygons if pv[f.vertices[0]]==5];pe=[tuple(e.vertices)for e in me.edges if all(pv[i]==5 for i in e.vertices)];se=[tuple(e.vertices)for e in me.edges if all(pv[i]==2 for i in e.vertices)];report={}
def intersections(co):
 out=[]
 for kind,fl,edges in [('pants_edges',sf,pe),('skirt_edges',pf,se)]:
  t=BVHTree.FromPolygons(co,fl)
  for a,b in edges:
   d=co[b]-co[a];L=d.length
   if L<1e-5:continue
   loc,n,fi,dist=t.ray_cast(co[a]+d.normalized()*1e-5,d.normalized(),L-2e-5)
   if loc is not None:out.append([kind,a,b,fi,list(loc)])
 return out
for n in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst=(0,0,[])
 for f in np.arange(0,float(a.frame_range[1])+1e-6,scene.render.fps/48):
  scene.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[body.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();hits=intersections(co)
  if len(hits)>worst[0]:worst=(len(hits),float(f/scene.render.fps),hits)
 report[n]={'max_crossing_edges':worst[0],'seconds':worst[1],'hits':worst[2]};print('SKIRT EDGES',n,worst[:2],flush=True)
(P/'review/skirt_intersections.json').write_text(json.dumps(report,indent=2))
