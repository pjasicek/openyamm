import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_twist.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data
co=np.array([tuple(v.co) for v in me.vertices]);parts=np.array([v.value for v in me.attributes['piece'].data]);names={g.index:g.name for g in ob.vertex_groups};groups={g.name:g for g in ob.vertex_groups}
def put(i,w):
 w={n:float(v)for n,v in w.items()if v>1e-7};total=sum(w.values());assert total>0
 for g in me.vertices[i].groups[:]:ob.vertex_groups[g.group].remove([i])
 for n,v in w.items():groups[n].add([i],v/total,'REPLACE')
for v in me.vertices:
 i=v.index;x,y,z=co[i];part=int(parts[i]);s='L'if x>0 else'R';w={names[e.group]:e.weight for e in v.groups}
 if part==1:
  t=float(np.clip((1.07-z)/.34,0,1));left=float(np.clip((x+.04)/.08,0,1));w={'B_Pelvis':1-t,'B_L_Thigh':t*left,'B_R_Thigh':t*(1-left)}
 elif part==2:
  t=float(np.clip((z-1.37)/.17,0,1));w={'B_Spine2':1-t,'B_Head':t}
 elif part==3:w={'B_Spine2':1}
 elif part in (4,9):w={'B_Pelvis':1}
 elif part in (5,6):w={f'B_{s}_ForearmTwist':1}
 elif part in (7,8,10,11):w={f'B_{s}_Foot':1}
 elif part==0:
  if z>1.45:
   t=float(np.clip((z-1.45)/.10,0,1));w={'B_Neck':1-t,'B_Head':t}
  elif abs(x)<.17 and 1.10<z<1.44:
   t=float(np.clip((abs(x)-.10)/.07,0,1));lost=0
   for n in list(w):
    if any(q in n for q in ['UpperArm','Forearm','Hand','Clavicle']):lost+=w[n]*(1-t);w[n]*=t
   w['B_Spine2']=w.get('B_Spine2',0)+lost
 put(i,w)
adj={v.index:[]for v in me.vertices if parts[v.index]==0}
for e in me.edges:
 a,b=e.vertices
 if a in adj and b in adj:adj[a].append(b);adj[b].append(a)
for _ in range(10):
 old={i:{names[e.group]:e.weight for e in me.vertices[i].groups}for i in adj}
 for i,nb in adj.items():
  if not nb or not(1.15<co[i,2]<1.43 and .10<abs(co[i,0])<.30):continue
  w={n:.5*v for n,v in old[i].items()}
  for j in nb:
   for n,v in old[j].items():w[n]=w.get(n,0)+.5*v/len(nb)
  put(i,w)
for v in me.vertices:
 w=sorted([(names[e.group],e.weight)for e in v.groups],key=lambda a:-a[1])[:4];put(v.index,dict(w));assert abs(sum(e.weight for e in v.groups)-1)<.001
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weighted.blend'))
