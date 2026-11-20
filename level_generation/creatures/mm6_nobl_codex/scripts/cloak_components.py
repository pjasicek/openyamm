import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'));o=bpy.data.objects['Body'];me=o.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv);ids=set(np.where(pv==0)[0]);adj={i:set() for i in ids}
for e in me.edges:
 a,b=e.vertices
 if a in ids and b in ids:adj[a].add(b);adj[b].add(a)
parts=[]
while ids:
 todo=[ids.pop()];comp=[]
 while todo:
  i=todo.pop();comp.append(int(i))
  for j in adj[i]&ids:ids.remove(j);todo.append(j)
 c=np.array([me.vertices[i].co[:] for i in comp]);parts.append(comp)
 print('COMP',len(comp),c.min(0).tolist(),c.max(0).tolist(),comp[:10])
(p/'review/feet_cloak_20261011/cloak_components.json').write_text(json.dumps(parts))
