from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];m=b.data;sc=bpy.context.scene
pc=np.array([v.value for v in m.attributes['piece'].data]);cr=np.array([v.value for v in m.attributes['cloth_region'].data]);co=np.array([tuple(v.co) for v in m.vertices]);gn=[g.name for g in b.vertex_groups]
print('REGIONS',[(int(i),np.unique(cr[pc==i]).tolist()) for i in np.unique(pc)])
print('SHOEBOX',co[pc==12].min(0),co[pc==12].max(0));faces=[tuple(f.vertices) for f in m.polygons if all(pc[i]==12 for i in f.vertices)]
a=bpy.data.actions['Running'];r.animation_data.action=a
if a.slots:r.animation_data.action_slot=a.slots[0]
worst=[]
for f in range(25):
 sc.frame_set(f);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons(pos.tolist(),faces)
 for i in np.where(cr==1)[0]:
  hit,n,face,dist=tree.find_nearest(Vector(pos[i]))
  if hit is not None and (Vector(pos[i])-hit).dot(n)<-.004:
   direction=Vector((1,.371,.237)).normalized();origin=Vector(pos[i]);crossings=0
   for _ in range(20):
    loc,_,_,_=tree.ray_cast(origin,direction)
    if loc is None:break
    crossings+=1;origin=loc+direction*.00001
   if crossings%2:worst.append(dict(frame=f,index=int(i),piece=int(pc[i]),rest=co[i].tolist(),posed=pos[i].tolist(),depth=dist,weights={gn[e.group]:e.weight for e in m.vertices[i].groups},hit_rest=co[list(faces[face])].tolist()))
worst=sorted(worst,key=lambda x:-x['depth']);(p/'work/shoe_contacts.json').write_text(json.dumps(worst,indent=2));print('WORST',worst[:3])
