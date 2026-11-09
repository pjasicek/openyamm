"""Blend thumb-web weights across their actual connected skin, including distal channels."""
import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_grip.blend'))
body=bpy.data.objects['Body'];me=body.data;nv=len(me.vertices)
W=np.zeros((nv,len(body.vertex_groups)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
nb=[[] for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices;nb[a].append(b);nb[b].append(a)
for sd in 'LR':
 chan=[g.index for g in body.vertex_groups if g.name==f'B_{sd}_Hand' or g.name.startswith(f'B_{sd}_Finger')]
 ww=W[:,chan].copy();tot=ww.sum(1);eligible=tot>.3
 # Four local averaging steps remove the distal-thumb/hand discontinuity at the web.
 for _ in range(4):
  wn=ww.copy()
  for i in np.where(eligible)[0]:
   near=[j for j in nb[i] if eligible[j]]
   if near:
    v=.5*ww[i]+.5*ww[near].mean(0);wn[i]=v/max(v.sum(),1e-12)*tot[i]
  ww=wn
 W[:,chan]=ww
for g in body.vertex_groups:g.remove(list(range(nv)))
for i,w in enumerate(W):
 assert abs(w.sum()-1)<.02,(i,w.sum())
 for j in np.where(w>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(w[j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_grip_smooth.blend'))
