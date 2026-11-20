"""Dwarf shell ownership; retain fitted hand topology for the connectivity pass."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2t.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);gs={g.name:g for g in ob.vertex_groups};names={g.index:g.name for g in ob.vertex_groups}
def put(i,w):
 for e in me.vertices[i].groups[:]:ob.vertex_groups[e.group].remove([i])
 w={n:float(v)for n,v in w.items()if v>1e-6};tot=sum(w.values());assert tot>0
 for n,v in w.items():gs[n].add([i],v/tot,'REPLACE')
def spine(z):
 zs=[.70,.83,.91,.99];ns=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];k=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[k])/(zs[k+1]-zs[k]),0,1));return{ns[k]:1-t,ns[k+1]:t}
for v in me.vertices:
 i=v.index;p=int(pv[i]);x,y,z=co[i];sd='L'if x>0 else 'R';w=None
 if p in [0,12,13]:w={'B_Head':1}
 elif p==1:
  w={names[e.group]:e.weight for e in v.groups if any(q in names[e.group]for q in ['Spine','Clavicle','UpperArm'])}
  cap=float(np.clip((abs(x)-.10)/.11,0,1))
  for n in list(w):
   if any(q in n for q in ['Clavicle','UpperArm']):w[n]*=cap
  if sum(w.values())<.01:w=spine(z)
 elif p in [3,4]:
  E=np.array(rig.data.bones[f'B_{sd}_Forearm'].head_local);W=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local);d=(W-E)/np.linalg.norm(W-E);t=float(np.clip(((co[i]-W)@d+.016)/.035,0,1));u=float(np.clip(((co[i]-E)@d+.035)/.065,0,1));w={f'B_{sd}_UpperArm':(1-u)*(1-t),f'B_{sd}_ForearmTwist':u*(1-t),f'B_{sd}_Hand':t}
 elif p in [9,10]:
  E=np.array(rig.data.bones[f'B_{sd}_Forearm'].head_local);S=np.array(rig.data.bones[f'B_{sd}_UpperArm'].head_local);d=(E-S)/np.linalg.norm(E-S);t=float(np.clip(((co[i]-E)@d+.045)/.09,0,1));w={f'B_{sd}_UpperArm':1-t,f'B_{sd}_Forearm':t}
 elif p==2:
  t=float(np.clip((.70-z)/.25,0,1))*.80;lr=float(np.clip((x+.10)/.20,0,1));w={'B_Pelvis':1-t,'B_L_Thigh':t*lr,'B_R_Thigh':t*(1-lr)}
 elif p==5:
  w={names[e.group]:e.weight for e in v.groups if any(q in names[e.group]for q in ['Pelvis','Thigh','Calf'])}
 elif p in [6,7]:
  t=float(np.clip((z-.15)/.08,0,1));w={f'B_{sd}_Foot':1-t,f'B_{sd}_Calf':t}
 elif p in [11,16,67]:w={'B_Pelvis':1}
 if w is not None:put(i,w)
# Yoke follows nearby shirt; each stud follows the large shell directly underneath.
kd=KDTree(int(np.isin(pv,[0,1,2,3,4,5,6,7,9,10,11]).sum()))
for i in np.where(np.isin(pv,[0,1,2,3,4,5,6,7,9,10,11]))[0]:kd.insert(co[i],int(i))
kd.balance()
for part in sorted(set(pv.tolist())):
 if part not in [8]and part<14:continue
 if part in [16,67]:continue
 ids=np.where(pv==part)[0]
 for i in ids:
  _,j,d=kd.find(co[i]);w={names[e.group]:e.weight for e in me.vertices[j].groups};put(int(i),w)
# Smooth the continuous shirt around the shoulder so small source weight noise cannot tear the sleeve.
adj={int(i):[]for i in np.where(pv==1)[0]}
for ed in me.edges:
 a,b=ed.vertices
 if a in adj and b in adj:adj[a].append(b);adj[b].append(a)
for _ in range(5):
 old={i:{names[e.group]:e.weight for e in me.vertices[i].groups}for i in adj}
 for i,ns in adj.items():
  if not ns:continue
  w={n:v*.65 for n,v in old[i].items()}
  for j in ns:
   for n,v in old[j].items():w[n]=w.get(n,0)+v*.35/len(ns)
  put(i,w)
for v in me.vertices:put(v.index,dict(sorted([(names[e.group],e.weight)for e in v.groups],key=lambda x:-x[1])[:4]))
assert all(abs(sum(e.weight for e in v.groups)-1)<.002 for v in me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'))
