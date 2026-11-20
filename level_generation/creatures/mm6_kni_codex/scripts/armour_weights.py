"""Knight piece ownership: armour stays on its limb; mesh fingers receive connectivity weights next."""
import bpy,sys,os,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2t.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value==8:
  z=v.co.z;t=max(0,min(1,(1.07-z)/.10));v.co.x*=1-.12*t
for v in me.vertices:
 if me.attributes['piece'].data[v.index].value==7:
  t=max(0,min(1,(1.52-v.co.z)/.2));v.co.x*=1-.22*t
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);gs={g.name:g for g in body.vertex_groups};names={g.index:g.name for g in body.vertex_groups}
def put(i,w):
 for g in me.vertices[i].groups[:]:body.vertex_groups[g.group].remove([i])
 w={n:float(v) for n,v in w.items() if v>1e-6};total=sum(w.values());assert total>0
 for n,v in w.items():gs[n].add([i],v/total,'REPLACE')
head={1,17,27,28,39,46,50}
# The remaining tiny components are knee fittings, shoulder spikes or bracer spikes, classified by measured position.
for v in me.vertices:
 i=v.index;part=int(pv[i]);x,y,z=co[i];s='L' if x>0 else 'R';w=None
 if part in (4,5):w={f'B_{s}_Hand':1}
 elif part in head:w={'B_Head':1}
 elif part in (15,16,21,22):w={'B_Neck':1}
 elif part==7:
  zs=[.98,1.16,1.35,1.52,1.68];ns=['B_Pelvis','B_Spine','B_Spine2','B_Neck','B_Head'];k=int(np.clip(np.searchsorted(zs,z)-1,0,3));t=float(np.clip((z-zs[k])/(zs[k+1]-zs[k]),0,1));w={ns[k]:1-t,ns[k+1]:t}
 elif part in (2,3) or (part>=18 and z>1.38 and abs(x)>.12):w={f'B_{s}_Clavicle':1}
 elif part in (9,10) or (part>=18 and .89<z<1.1 and abs(x)>.3):w={f'B_{s}_ForearmTwist':1}
 elif part in (11,12):w={f'B_{s}_Calf':1}
 elif part in (13,14):w={f'B_{s}_Foot':1}
 elif part in (19,20,40,42,43,45,48,49):w={f'B_{s}_Calf':.7,f'B_{s}_Thigh':.3}
 elif part in (23,24,25,26,29,30,37,38):w={f'B_{s}_Forearm':.7,f'B_{s}_UpperArm':.3}
 elif part==18:w={'B_Spine2':1}
 elif part in (8,44):
  # Short plate fauld: sides follow the local thigh, belt stays at pelvis.
  t=float(np.clip((1.065-z)/.30,0,1));w={'B_Pelvis':1-t*.8,f'B_{s}_Thigh':t*.8}
 elif part==6:
  w={names[e.group]:e.weight for e in v.groups if any(t in names[e.group] for t in ['Pelvis','Thigh','Calf'])}
 if w is not None:put(i,w)
# Diffuse noisy transferred weights over the connected underarm sleeve, before quantising to four influences.
adj={v.index:[] for v in me.vertices if pv[v.index]==0}
for e in me.edges:
 a,b=e.vertices
 if a in adj and b in adj:adj[a].append(b);adj[b].append(a)
for _ in range(10):
 old={i:{names[g.group]:g.weight for g in me.vertices[i].groups} for i in adj}
 for i,nb in adj.items():
  if not nb or abs(co[i,0])<.10 or co[i,2]<1.14:continue
  w={n:.5*v for n,v in old[i].items()}
  for j in nb:
   for n,v in old[j].items():w[n]=w.get(n,0)+.5*v/len(nb)
  put(i,w)
# Runtime uses four weights; perform that exact reduction before gates.
for v in me.vertices:
 w=sorted([(names[g.group],g.weight) for g in v.groups],key=lambda x:-x[1])[:4];put(v.index,dict(w))
for v in me.vertices:assert abs(sum(e.weight for e in v.groups)-1)<.002
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'))
print('ARMOUR ownership assigned',len(me.vertices))
