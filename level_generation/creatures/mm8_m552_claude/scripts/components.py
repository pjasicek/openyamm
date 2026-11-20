import bpy, bmesh, json, sys
import numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
V = sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'v1'
bpy.ops.wm.open_mainfile(filepath=str(p/f'work/import_{V}.blend'))
o=next(o for o in bpy.data.objects if o.type=='MESH')
co=np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
adj=[[] for v in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();parts=[]
for v in range(len(co)):
 if v in seen:continue
 seen.add(v);stack=[v];part=[]
 while stack:
  a=stack.pop();part.append(a)
  for b in adj[a]:
   if b not in seen:seen.add(b);stack.append(b)
 parts.append(part)
parts.sort(key=len,reverse=True)
report=[dict(id=i,n=len(x),lo=co[x].min(0).round(5).tolist(),hi=co[x].max(0).round(5).tolist(),mean=co[x].mean(0).round(5).tolist()) for i,x in enumerate(parts)]
(p/f'work/components_{V}.json').write_text(json.dumps(dict(report=report,vertices=parts),indent=2)+'\n')
print(json.dumps(report))
