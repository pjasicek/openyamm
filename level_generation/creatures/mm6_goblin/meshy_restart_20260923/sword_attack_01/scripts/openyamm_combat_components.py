import bpy,json
from pathlib import Path
s=bpy.data.scenes['Goblin - Sword and Native Attack'];m=s.objects['Goblin_Combat_Body'];p=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');garment=set(i for c in json.loads((p/'strips.json').read_text()) for i in c['ids']);parents=list(range(len(m.data.vertices)))
def find(i):
 while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
 return i
def union(a,b):parents[find(a)]=find(b)
coinc={}
for v in m.data.vertices:
 if v.index in garment:continue
 key=tuple(round(c,5) for c in v.co)
 if key in coinc:union(v.index,coinc[key])
 else:coinc[key]=v.index
for e in m.data.edges:
 if all(i not in garment for i in e.vertices):union(*e.vertices)
parts={}
for v in m.data.vertices:
 if v.index not in garment:parts.setdefault(find(v.index),[]).append(v.index)
parts=sorted(parts.values(),key=len,reverse=True);report=[]
for ids in parts:
 co=[m.matrix_world@m.data.vertices[i].co for i in ids];report.append({'n':len(ids),'min':[min(c[k] for c in co) for k in range(3)],'max':[max(c[k] for c in co) for k in range(3)],'ids':ids})
(p/'body_components.json').write_text(json.dumps(report));print(json.dumps([{k:v for k,v in x.items() if k!='ids'} for x in report[:15]]))
