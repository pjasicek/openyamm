"""Focused numerical review of the new viewer motions, without touching the production master."""
from pathlib import Path
import bpy, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
out=p/'review/motion_options'
bpy.ops.wm.open_mainfile(filepath=str(out/'ogre_motion_options.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Ogre'];me=body.data;sc=bpy.context.scene
sources=json.loads((out/'sources.json').read_text())
names={g.index:g.name for g in body.vertex_groups}
dom=[names[max(v.groups,key=lambda e:e.weight).group] if v.groups else '' for v in me.vertices]
sword=[v.index for v in me.vertices if dom[v.index]=='Sword']
exclude=lambda i: dom[i]=='Sword' or dom[i].startswith(('B_R_Hand','B_R_Finger'))
polys=[tuple(f.vertices) for f in me.polygons if not any(exclude(i) for i in f.vertices)]
rest=[v.co.copy() for v in me.vertices]
handedges=[tuple(e.vertices) for e in me.edges if all(dom[i].startswith(('B_R_Hand','B_R_Finger','B_L_Hand','B_L_Finger')) for i in e.vertices)]
report={}
for name,source in sources.items():
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 worst=[0,None,None];stretch=0;start=None;end=None
 for frame in range(int(a.frame_range[1])*2+1):
  t=frame/2;sc.frame_set(int(t),subframe=t%1)
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
  co=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
  tree=BVHTree.FromPolygons(co,polys)
  for i in sword[::2]:
   loc,n,fi,d=tree.find_nearest(co[i],.15)
   if loc is not None and d>worst[0] and d>1e-6 and (co[i]-loc).dot(n)<-.707*d:
    worst=[d,t/30,dom[polys[fi][0]]]
  for i,j in handedges:
   length=(rest[i]-rest[j]).length
   if length>1e-5:stretch=max(stretch,(co[i]-co[j]).length/length)
  for pb in rig.pose.bones:
   assert all(math.isfinite(v) for row in pb.matrix for v in row),(name,t,pb.name)
   assert max(abs(v-1) for v in pb.scale)<1e-5,(name,t,pb.name,'scale')
  pose={b.name:b.rotation_quaternion.copy() for b in rig.pose.bones}
  if start is None:start=pose
  end=pose
 loop=max(math.degrees(min(q.rotation_difference(end[n]).angle,2*math.pi-q.rotation_difference(end[n]).angle)) for n,q in start.items())
 assert abs((a.frame_range[1]-a.frame_range[0])/30-source['duration'])<1e-6
 report[name]={'sword_body_depth_m':worst[0],'sword_contact_seconds':worst[1],'body_region':worst[2],
               'hand_edge_stretch_max':stretch,'endpoint_rotation_difference_degrees':loop}
 print('MOTION_CHECK',name,report[name],flush=True)
(out/'checks').mkdir(exist_ok=True)
(out/'checks/geometry.json').write_text(json.dumps(report,indent=2)+'\n')
