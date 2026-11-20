"""Hand vertices against each solid part of the actual rigid crossbow throughout motion."""
import os,bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('M632_CHECK_BLEND','work/motion_native.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow'];sc=bpy.context.scene
pv=np.array([x.value for x in body.data.attributes['piece'].data]);ids=np.where(np.isin(pv,(7,8)))[0]
weapon=np.array([v.co[:] for v in prop.data.vertices]);adj=[set() for _ in weapon]
for e in prop.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
components=[];seen=set()
for i in range(len(weapon)):
 if i in seen:continue
 todo=[i];part=set()
 while todo:
  v=todo.pop()
  if v in part:continue
  part.add(v);todo.extend(adj[v]-part)
 seen|=part;faces=[tuple(p.vertices) for p in prop.data.polygons if p.vertices[0] in part]
 pts=weapon[list(part)];components.append((BVHTree.FromPolygons(weapon.tolist(),faces),pts.min(0),pts.max(0)))
report={}
for name in ('Standing','Walking','Running','Attack','Hit','Death','Fidget','Dead'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={}
 for f in np.arange(*[a.frame_range[0],a.frame_range[1]+.01],sc.render.fps/120):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  inv=(rig.matrix_world@rig.pose.bones['Crossbow'].matrix@rig.data.bones['Crossbow'].matrix_local.inverted()).inverted()
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  pts=np.array([tuple(inv@body.matrix_world@me.vertices[int(i)].co) for i in ids]);ev.to_mesh_clear()
  for ci,(tree,lo,hi) in enumerate(components):
   selected=np.where(np.all(pts>=lo,axis=1)&np.all(pts<=hi,axis=1))[0]
   for k in selected:
    loc,norm,face,d=tree.find_nearest(Vector(pts[k]));side='L' if pv[ids[k]]==7 else 'R'
    if (Vector(pts[k])-loc).dot(norm)<-1e-5 and d>worst.get(side,{}).get('depth_m',.001):worst[side]={'depth_m':d,'frame':float(f),'component':ci,'vertex':int(ids[k])}
 report[name]=worst;print('HAND PROP CONTACT',name,worst,flush=True)
(P/'work/grip_contacts.json').write_text(json.dumps(report,indent=2))
