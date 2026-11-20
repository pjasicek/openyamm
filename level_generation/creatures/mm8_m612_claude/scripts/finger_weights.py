"""Bind each curved claw by mesh connectivity and distance along its branch."""
import bpy,json,sys,heapq
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=str(Path(src).resolve()))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
fit=json.loads((P/'work/fingers_fit.json').read_text())
co=np.array([tuple(v.co) for v in me.vertices])
groups={g.name:g for g in body.vertex_groups}
labels=np.zeros(len(co),np.int32)
for side in 'LR':
 hand=groups[f'B_{side}_Hand']
 weight=np.array([sum(e.weight for e in v.groups if e.group==hand.index) for v in me.vertices])
 ids=set(np.where(weight>.05)[0].tolist())
 adj={i:[] for i in ids}
 for e in me.edges:
  a,b=e.vertices
  if a in ids and b in ids:
   length=float(np.linalg.norm(co[a]-co[b]));adj[a].append((b,length));adj[b].append((a,length))
 mapping={0:'thumb',1:'index',2:'middle',4:'pinky'}
 owner={int(i):f for f,name in mapping.items() for i in fit[side]['verts'][name]}
 dist={i:0.0 for i in owner};heap=[(0.0,i,f) for i,f in owner.items()];heapq.heapify(heap)
 while heap:
  d,i,f=heapq.heappop(heap)
  if d>dist[i]:continue
  for j,length in adj.get(i,[]):
   nd=d+length
   if nd<dist.get(j,float('inf')):
    dist[j]=nd;owner[j]=f;heapq.heappush(heap,(nd,j,f))
 depth={int(i):d for i,d in fit[side]['geodesic_depth'].items()}
 limits={f:(min(depth[i] for i in fit[side]['verts'][name])-.022,
            max(depth[i] for i in fit[side]['verts'][name])) for f,name in mapping.items()}
 chains={}
 for f in mapping:
  chain=[f'B_{side}_Finger{f}']
  while True:
   kids=[b.name for b in rig.data.bones if b.parent and b.parent.name==chain[-1]]
   if not kids:break
   chain.append(kids[0])
  assert len(chain)==3
  chains[f]=chain
 assigned={f:0 for f in mapping}
 new={}
 for i in ids:
  if i not in owner or i not in depth:continue
  f=owner[i];lo,hi=limits[f];t=(depth[i]-lo)/(hi-lo)
  if t<-.12:continue
  chain=chains[f]
  # The measured curved branch stays ordered even where its hook folds back beside the palm.
  w={hand.name:1-float(np.clip((t+.12)/.24,0,1)),chain[0]:float(np.clip((t+.12)/.24,0,1))}
  if t>.12:
   w={chain[0]:1.0}
   for j,boundary in ((1,.38),(2,.72)):
    amount=float(np.clip((t-boundary+.08)/.16,0,1))
    if amount>0:
     w={chain[j-1]:1-amount,chain[j]:amount}
  new[i]={n:v*weight[i] for n,v in w.items()}
  labels[i]=f+1;assigned[f]+=1
 # Smooth only the proximal web; tips remain on their own distal phalanx.
 channels=[hand.name]+[chains[f][0] for f in mapping]
 W=np.zeros((len(co),len(channels)))
 for i in ids:
  current=new.get(i,{hand.name:weight[i]})
  for j,n in enumerate(channels):W[i,j]=current.get(n,0)
 for _ in range(3):
  nxt=W.copy()
  for i in ids:
   if i not in new or W[i].sum()<weight[i]*.95:continue
   ns=[j for j,_ in adj[i] if W[j].sum()>0.05]
   if ns:
    blend=.7*W[i]+.3*W[ns].mean(0)
    nxt[i]=blend/max(blend.sum(),1e-9)*W[i].sum()
  W=nxt
 for i in new:
  if W[i].sum()>weight[i]*.95:new[i]={n:W[i,j] for j,n in enumerate(channels)}
  total=sum(new[i].values());assert total>0
  new[i]={n:w*weight[i]/total for n,w in new[i].items()}
  hand.remove([i])
  for n,w in new[i].items():
   if w>1e-5:groups[n].add([i],float(w),'REPLACE')
 assert all(n>20 for n in assigned.values()),assigned
 print('FINGER_BIND',side,assigned)
a=me.attributes.get('finger') or me.attributes.new('finger','INT','POINT')
a.data.foreach_set('value',labels)
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out).resolve()))
