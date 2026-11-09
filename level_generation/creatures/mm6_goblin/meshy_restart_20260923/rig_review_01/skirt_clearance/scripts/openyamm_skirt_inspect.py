import bpy,json
from pathlib import Path
s=bpy.context.scene
print('CURRENT',s.name,s.frame_current)
for o in s.objects:
 if o.type=='ARMATURE':print('ARM',o.name,o.animation_data.action.name if o.animation_data and o.animation_data.action else None)
s=bpy.data.scenes['Goblin - Upright Rig Review'];m=next(o for o in s.objects if o.type=='MESH');uv=m.data.uv_layers.active.data;ids=set()
for p in m.data.polygons:
 if any(uv[i].uv.x>.49999 or uv[i].uv.y>.49999 for i in p.loop_indices):ids.update(p.vertices)
adj={i:set() for i in ids}
for e in m.data.edges:
 a,b=e.vertices
 if a in ids and b in ids:adj[a].add(b);adj[b].add(a)
comps=[];left=set(ids)
while left:
 todo=[left.pop()];part=[]
 while todo:
  i=todo.pop();part.append(i)
  for j in adj[i]:
   if j in left:left.remove(j);todo.append(j)
 comps.append(part)
report=[]
for p in comps:
 co=[m.matrix_world@m.data.vertices[i].co for i in p];report.append({'n':len(p),'min':[min(c[k] for c in co) for k in range(3)],'max':[max(c[k] for c in co) for k in range(3)],'ids':p})
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/skirt_clearance');OUT.mkdir(exist_ok=True);(OUT/'components.json').write_text(json.dumps(report));print('MESH',m.name,'components',len(comps));print(json.dumps([{k:v for k,v in c.items() if k!='ids'} for c in report]))
