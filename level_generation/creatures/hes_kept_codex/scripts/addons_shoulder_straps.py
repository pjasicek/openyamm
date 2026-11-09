import bpy,sys,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];path=P/'work/addons_v2/equipped.blend';bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['hes_kept_plate'];adj={v.index:set()for v in o.data.vertices}
for e in o.data.edges:a,b=e.vertices;adj[a].add(b);adj[b].add(a)
unseen=set(adj);moved=[]
while unseen:
 ids={unseen.pop()};todo=list(ids)
 while todo:
  for j in adj[todo.pop()]-ids:ids.add(j);todo.append(j)
 unseen-=ids;zs=[o.data.vertices[i].co.z for i in ids]
 if min(zs)<1.30 or max(zs)<1.39:continue
 cx=sum(o.data.vertices[i].co.x for i in ids)/len(ids);dx=.012 if cx>-.03255 else -.012
 for i in ids:o.data.vertices[i].co.x+=dx
 moved.append({'vertices':len(ids),'outward_x_m':dx})
assert len(moved)==2,moved
bpy.ops.wm.save_as_mainfile(filepath=str(path));(P/'review/addons_v2/shoulder_straps.json').write_text(json.dumps(moved,indent=2)+'\n');print('SHOULDER_STRAPS',moved,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
