from pathlib import Path
P=Path(__file__).resolve().parents[1];s=P/'scripts/equipment_checks.py';exec(compile(s.read_text().split('for a in list(bpy.data.actions):')[0],str(s),'exec'))
for name,f in [('Running',10),('Walking',12),('Death',36)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(f),subframe=f%1);co=coords(o);part,fs=proxies[2];tree=BVHTree.FromPolygons(co,fs);qo=bpy.data.objects['QuiverMesh'];pc=coords(qo);best=None
 for i,point in enumerate(pc):
  hit,norm,idx,d=tree.find_nearest(Vector(point),.07)
  if hit is not None and d>.002 and (Vector(point)-hit).dot(norm)<-.7*d and inside(tree,point) and (best is None or d>best[0]):best=(d,i,point,hit,norm,idx)
 if best:
  d,i,point,hit,norm,idx=best;weights={}
  for vi in fs[idx]:
   for g in me.vertices[vi].groups:weights[o.vertex_groups[g.group].name]=weights.get(o.vertex_groups[g.group].name,0)+g.weight
  Q=r.pose.bones['Quiver'].matrix;print('QUIVER_CONTACT',name,f,'depth',d,'local',list(Q.inverted()@Vector(point)),'normal',list(Q.to_3x3().inverted()@norm),'body',sorted(weights.items(),key=lambda x:-x[1])[:3],flush=True)
