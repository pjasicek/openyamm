"""Smooth short-edge weight discontinuities on the upper arm while preserving hand/finger weights."""
import bpy,numpy as np,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for blend in ['rig_v5.blend','rig_v6.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(p/'work'/blend.replace('.blend','_pre_arm_polish.blend')));o=bpy.data.objects['Body'];me=o.data;nv=len(me.vertices);W=np.zeros((nv,len(o.vertex_groups)))
 for v in me.vertices:
  for e in v.groups:W[v.index,e.group]=e.weight
 nb=[[] for _ in me.vertices]
 for e in me.edges:
  a,b=e.vertices;nb[a].append(b);nb[b].append(a)
 arm=[g.index for g in o.vertex_groups if any(n in g.name for n in ('UpperArm','Forearm'))]
 hands=[g.index for g in o.vertex_groups if 'Hand' in g.name or 'Finger' in g.name]
 eligible=(W[:,arm].sum(1)>.1)&(W[:,hands].sum(1)<.1)
 for _ in range(8):
  new=W.copy()
  for i in np.where(eligible)[0]:
   if nb[i]:new[i]=.5*W[i]+.5*W[nb[i]].mean(0)
  W=new
 retained=[]
 for i in range(nv):
  w=W[i].copy();keep=np.argsort(w)[-8:];total=w[keep].sum();retained.append(float(total));W[i]=0;W[i,keep]=w[keep]/total
 assert min(retained)>.95,min(retained)
 print('PRUNE minimum retained mass',min(retained))
 for g in o.vertex_groups:g.remove(list(range(nv)))
 for i,w in enumerate(W):
  assert abs(w.sum()-1)<.02
  for j in np.where(w>1e-6)[0]:o.vertex_groups[int(j)].add([i],float(w[j]),'REPLACE')
 bpy.ops.wm.save_as_mainfile(filepath=str(p/'work'/blend))
s=p/'scripts/g4_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_v5.blend'),'smooth','Standing:0','Attack:25','Attack:28','Attack:34','Walking:6','Running:6','Death:20'];runpy.run_path(str(s),run_name='__main__')
