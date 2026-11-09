"""Check whether internal trousers contribute any exterior surface in all role extrema and eight views."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/round3_lod0.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;pv=[x.value for x in body.data.attributes['piece'].data];faces=[tuple(f.vertices) for f in body.data.polygons];ids=[i for i,f in enumerate(faces) if all(pv[v] in [103,104] for v in f)];visible=set();report={}
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];seen=set()
 for k in range(5):
  f=a.frame_range[1]*k/4;scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces)
  for i in ids:
   pt=sum((co[j] for j in faces[i]),Vector())/len(faces[i])
   for view in range(8):
    d=Vector((math.sin(view*math.pi/4),math.cos(view*math.pi/4),.10)).normalized();q,n,ix,distance=tree.ray_cast(pt+d*5,-d,5.001)
    if q is not None and abs(distance-5)<.0003:seen.add(i);break
 visible|=seen;report[role]={'visible_faces':len(seen),'rest_z_range':[min((body.data.vertices[j].co.z for i in seen for j in faces[i]),default=0),max((body.data.vertices[j].co.z for i in seen for j in faces[i]),default=0)]}
report['total_visible_faces']=len(visible);print('PANTS_VISIBILITY',json.dumps(report),flush=True);(p/'work/pants_visibility_r3.json').write_text(json.dumps(report,indent=2))
