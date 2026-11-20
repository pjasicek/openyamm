"""Check the thin native wrap separately from the closed skin."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/('work/'+__import__('os').environ.get('M480_MOTION_FILE','reduced.blend'))))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;pv=np.array([x.value for x in me.attributes['piece'].data]);rest=np.array([tuple(v.co) for v in me.vertices]);e=np.array([tuple(x.vertices) for x in me.edges]);lens=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
cloth=[1,2,16,17,65];ce=(np.isin(pv[e[:,0]],cloth)&np.isin(pv[e[:,1]],cloth));faces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==0 for i in f.vertices)];ids=np.where(np.isin(pv,cloth)&(rest[:,2]<.81))[0];out={}
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];row={'stretch_max':0,'stretch_p99':0,'skin_penetration_m':0,'visible_hem_depth_m':0}
 for f in np.arange(0,act.frame_range[1]+.01,2):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();rat=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1)/np.maximum(lens,1e-6);row['stretch_max']=max(row['stretch_max'],float(rat[ce].max()));row['stretch_p99']=max(row['stretch_p99'],float(np.percentile(rat[ce],99)))
  tree=BVHTree.FromPolygons(co.tolist(),faces)
  for i in ids:
   v=Vector(co[i]);loc,n,ix,d=tree.find_nearest(v)
   if (v-loc).dot(n)<-.7*d:
    direction=Vector((.713,.429,.555)).normalized();origin=v+direction*.00001;hits=0
    for _ in range(40):
     point,normal,face,distance=tree.ray_cast(origin,direction,4)
     if point is None:break
     hits+=1;origin=point+direction*.00003
    if hits%2:
     if d>row['skin_penetration_m']:row.update(skin_penetration_m=d,frame=float(f),vertex=int(i),piece=int(pv[i]),rest_position=rest[i].tolist())
     if rest[i,2]<.70 and d>row['visible_hem_depth_m']:row.update(visible_hem_depth_m=d,hem_frame=float(f),hem_vertex=int(i),hem_position=rest[i].tolist())
 out[act.name]=row;print('CLOTH',act.name,row,flush=True)
(p/'review/cloth_probe.json').write_text(json.dumps(out,indent=2))
