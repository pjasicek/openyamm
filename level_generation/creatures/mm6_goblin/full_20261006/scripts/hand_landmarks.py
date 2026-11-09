import bpy,json
from pathlib import Path
from mathutils import Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/body_corrected_v1.blend'))
o=bpy.data.objects['GoblinBody_Corrected'];groups={g.index:g.name for g in o.vertex_groups}
skin={v.index for v in o.data.vertices if any(groups[g.group]=='Component_0' for g in v.groups)}
edges={i:set() for i in skin}
for e in o.data.edges:
 a,b=e.vertices
 if a in skin and b in skin:edges[a].add(b);edges[b].add(a)
report={}
for side,sign in [('R',-1),('L',1)]:
 report[side]={}
 for cut in (.74,.70,.68,.66,.64):
  todo={i for i in skin if sign*o.data.vertices[i].co.x>.48 and o.data.vertices[i].co.z<cut};components=[]
  while todo:
   work=[todo.pop()];found=set(work)
   while work:
    i=work.pop()
    for j in edges[i]&todo:todo.remove(j);found.add(j);work.append(j)
   p=[o.data.vertices[i].co for i in found]
   components.append({'vertices':sorted(found),'count':len(found),'min':[min(v[a] for v in p) for a in range(3)],'max':[max(v[a] for v in p) for a in range(3)],'center':list(sum(p,Vector())/len(p))})
  report[side][str(cut)]=components
  print(side,cut,[{k:v for k,v in c.items() if k!='vertices'} for c in components],flush=True)
(OUT/'review/rig/hand_segments.json').write_text(json.dumps(report,indent=2)+'\n')
