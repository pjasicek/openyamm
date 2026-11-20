import bpy,json,numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=o.data;piece=[x.value for x in me.attributes['piece'].data];faces=[list(f.vertices) for f in me.polygons if piece[f.vertices[0]]==0];caps=json.loads((P/'work/feedback_geometry.json').read_text())['arms'];report={}
def inside(tree,p):
 # Nearest-face normals misclassify points near a concave cuff corner; the garment is a closed surface.
 votes=[]
 for direction in [(1,.23,.17),(-.31,1,.27),(.19,-.29,1)]:
  d=Vector(direction).normalized();origin=p.copy();crossings=0
  for _ in range(50):
   q,n,i,dist=tree.ray_cast(origin,d,4.)
   if q is None:break
   crossings+=1;origin=q+d*1e-5
  votes.append(crossings%2==1)
 return sum(votes)>=2
for name in ['Standing','Walking','Fidget','Hit','Death','Dead']:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst={s:-1 for s in caps};at={}
 for frame in range(int(a.frame_range[1])+1):
  bpy.context.scene.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,faces,all_triangles=True)
  for side,info in caps.items():
   for vi in info['cap_vertices']:
    q,n,_,dist=tree.find_nearest(co[vi]);signed=-dist if inside(tree,co[vi]) else dist
    if signed>worst[side]:worst[side]=signed;at[side]=frame
 report[name]={'maximum_outside_m':worst,'worst_frame':at}
print('CUFF_CAPS',json.dumps(report),flush=True);(P/'work/cuff_cap_check.json').write_text(json.dumps(report,indent=2))
assert max(v for x in report.values() for v in x['maximum_outside_m'].values())<.002
