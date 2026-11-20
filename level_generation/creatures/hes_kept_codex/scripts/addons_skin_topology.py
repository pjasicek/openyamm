import bpy,sys,os,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/addons_v2/equipped.blend'));b=bpy.data.objects['Kept'];pc=[v.value for v in b.data.attributes['piece'].data]
for part in (0,1,3,4):
 fs=[tuple(p.vertices)for p in b.data.polygons if pc[p.vertices[0]]==part];edges=collections.Counter(tuple(sorted((f[i],f[(i+1)%3])))for f in fs for i in range(3));print('TOPOLOGY',part,len(fs),collections.Counter(edges.values()),flush=True)
 adj=collections.defaultdict(set)
 for f in fs:
  for i in f:adj[i].update(f)
 unseen=set(adj);parts=[]
 while unseen:
  ids={unseen.pop()};todo=list(ids)
  while todo:
   for j in adj[todo.pop()]-ids:ids.add(j);todo.append(j)
  unseen-=ids;ff=[f for f in fs if f[0] in ids];e=collections.Counter(tuple(sorted((f[i],f[(i+1)%3])))for f in ff for i in range(3));ps=[b.data.vertices[i].co for i in ids];parts.append((len(ids),len(ff),dict(collections.Counter(e.values())),min(p.z for p in ps),max(p.z for p in ps)))
 print('COMPONENTS',part,parts,flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
