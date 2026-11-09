from pathlib import Path
import bpy,json,numpy as np
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];c=bpy.data.objects['Club'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
d=bpy.context.evaluated_depsgraph_get();ev=c.evaluated_get(d);me=ev.to_mesh();tree=BVHTree.FromPolygons([c.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);ev.to_mesh_clear()
ev=b.evaluated_get(d);me=ev.to_mesh();report={}
for label in [1,2,3,5]:
 ids=[v.index for v in b.data.vertices if v.co.x<0 and b.data.attributes['finger'].data[v.index].value==label]
 hits=[]
 for i in ids:
  pos=b.matrix_world@me.vertices[i].co;loc,n,idx,dist=tree.find_nearest(pos);hits.append(dist*(1 if (pos-loc).dot(n)>=0 else -1))
 report[str(label)]={'nearest_signed_distance_m':min(hits),'closest_surface_distance_m':min(abs(v) for v in hits),'penetrating_vertices':sum(v<-.001 for v in hits),'vertices':len(ids)}
ev.to_mesh_clear();(p/'review/actual_grip_contact.json').write_text(json.dumps(report,indent=2));print('ACTUAL GRIP',json.dumps(report))
