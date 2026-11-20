from pathlib import Path
import bpy,json,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_body.blend'))
ob=bpy.data.objects['Body'];me=ob.data;pv=[x.value for x in me.attributes['piece'].data]
co=np.array([tuple(v.co) for v in me.vertices]);edges=[tuple(e.vertices) for e in me.edges if all(pv[i]==1 for i in e.vertices)]
report={}
for height in [1.25,1.16,1.05,.98,.92,.86,.80]:
 ids={i for i,x in enumerate(pv) if x==1 and co[i,2]<height};adj={i:[] for i in ids}
 for a,b in edges:
  if a in ids and b in ids:adj[a].append(b);adj[b].append(a)
 groups=[]
 while ids:
  seed=ids.pop();todo=[seed];group=[seed]
  while todo:
   for n in adj[todo.pop()]:
    if n in ids:ids.remove(n);todo.append(n);group.append(n)
  if len(group)>5:groups.append({'n':len(group),'min':co[group].min(0).tolist(),'max':co[group].max(0).tolist(),'mean':co[group].mean(0).tolist(),'ids':group})
 report[str(height)]=sorted(groups,key=lambda x:-x['n'])
 print('GARMENT_COMPONENTS',height,[{k:v for k,v in x.items() if k!='ids'} for x in report[str(height)]],flush=True)
(p/'work/garment_components.json').write_text(json.dumps(report,indent=2)+'\n')
