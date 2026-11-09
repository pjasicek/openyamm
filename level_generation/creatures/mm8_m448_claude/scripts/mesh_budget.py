from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_final.blend'))
body=bpy.data.objects['Body'];me=body.data;pv=[v.value for v in me.attributes['piece'].data]
per={}
for f in me.polygons:
    n=pv[f.vertices[0]];per[n]=per.get(n,0)+len(f.vertices)-2
print('PIECES',per)
adj=[[] for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();parts=[]
for v in me.vertices:
 if pv[v.index]!=200 or v.index in seen:continue
 stack=[v.index];ids=[]
 while stack:
  i=stack.pop()
  if i in seen:continue
  seen.add(i);ids.append(i);stack.extend(j for j in adj[i] if j not in seen)
 coords=[me.vertices[i].co for i in ids]
 parts.append({'verts':len(ids),'lo':[min(v[k] for v in coords) for k in range(3)],'hi':[max(v[k] for v in coords) for k in range(3)]})
parts.sort(key=lambda x:-x['verts']);print('HEAD_COMPONENTS',json.dumps(parts[:12]))
(p/'work/mesh_budget.json').write_text(json.dumps({'pieces':per,'head_components':parts},indent=2))
