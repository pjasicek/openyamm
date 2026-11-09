import bpy,numpy as np,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_body.blend'));ob=bpy.data.objects['Body'];me=ob.data;pv=np.array([a.value for a in me.attributes['piece'].data]);N=len(me.vertices);G=len(ob.vertex_groups);W=np.zeros((N,G));adj=[[]for _ in range(N)]
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]:adj[a].append(b);adj[b].append(a)
ids=[int(i)for i in np.where(np.isin(pv,[1,8]))[0]if me.vertices[i].co.z>.775]
for _ in range(12):
 next=W.copy()
 for i in ids:
  ns=adj[i]
  if ns:next[i]=W[i]*.6+W[ns].mean(0)*.4
 W=next
for i in ids:
 w=W[i];order=np.argsort(-w)[:4];w4=w[order];w4/=w4.sum()
 for e in me.vertices[i].groups[:]:ob.vertex_groups[e.group].remove([i])
 for g,v in zip(order,w4):
  if v>1e-7:ob.vertex_groups[int(g)].add([i],float(v),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_body.blend'))
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];picks=[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,2)]
sys.argv=['g4_weights.py','--',str(P/'work/production_body.blend'),'final_body',*picks];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
