from pathlib import Path
import bpy,json,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));me=bpy.data.objects['Body'].data;co=np.array([tuple(v.co) for v in me.vertices]);adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
def comps(mask):
 left=set(np.flatnonzero(mask).tolist());out=[]
 while left:
  st=[left.pop()];vs=[]
  while st:
   a=st.pop();vs.append(a)
   for b in adj[a]:
    if b in left:left.remove(b);st.append(b)
  if len(vs)>3:out.append(vs)
 return out
results=[]
for y in (-.41,-.43,-.45,-.46,-.47,-.48):
 for x in (.1,.12,.14):
  cs=comps((abs(co[:,0])<x)&(co[:,1]<y)&(co[:,2]>1.105)&(co[:,2]<1.31));rec=[]
  for c in cs:
   b=co[c];rec.append({'vertices':c,'count':len(c),'min':b.min(0).tolist(),'max':b.max(0).tolist(),'upper_roots':int((b[:,2]>1.26).sum()),'lower_roots':int((b[:,2]<1.145).sum())})
  results.append({'x':x,'y':y,'components':rec});print('DENTAL_CUT',x,y,[{k:v for k,v in a.items() if k!='vertices'} for a in rec],flush=True)
(P/'work/dental_cuts.json').write_text(json.dumps(results,indent=2)+'\n')
