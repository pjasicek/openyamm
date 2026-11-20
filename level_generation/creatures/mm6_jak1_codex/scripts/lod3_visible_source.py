"""Remove buried faces only from the distant LOD source, testing all eight clips and sixteen directions."""
import bpy,bmesh,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];W=P/'work/round2/reduction';bpy.ops.wm.open_mainfile(filepath=str(W/'unreduced.blend'));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data;faces=[tuple(f.vertices)for f in me.polygons];visible=np.array([f.material_index==2 for f in me.polygons]);directions=[Vector((math.sin(a),math.cos(a),z)).normalized()for z in [.05,.6]for a in np.arange(8)*math.pi/4];snapshots=[]
for name in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
 for frame in np.linspace(*action.frame_range,5 if name not in ['Standing','Dead']else 1):
  sc.frame_set(int(frame),subframe=float(frame-int(frame)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=[v.co.copy()for v in mesh.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces)
  for i in np.flatnonzero(~visible):
   pts=[co[j]for j in faces[i]];center=sum(pts,Vector())/len(pts)
   for d in directions:
    if any(tree.ray_cast(q+d*.00002,d,10)[0]is None for q in [center,*[(center+v)*.5 for v in pts]]):visible[i]=True;break
  snapshots.append({'clip':name,'frame':float(frame),'visible_faces':int(visible.sum())});print('VISIBLE SOURCE',name,round(frame,1),int(visible.sum()),len(visible),flush=True)
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i]for i in np.flatnonzero(~visible)],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(me);bm.free();rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'visible_source.blend'));(P/'review/round2/reduction/visible_source.json').write_text(json.dumps({'source':'work/round2/reduction/unreduced.blend','faces_before':len(visible),'faces_retained':int(visible.sum()),'snapshots':snapshots,'directions':16,'samples':'centroid and each centre-to-corner midpoint','scope':'LOD3 source only; hidden faces remain in LOD0-2'},indent=2))
