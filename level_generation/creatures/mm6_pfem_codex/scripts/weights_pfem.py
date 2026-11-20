"""Skin the repaired peasant from fitted anatomical regions; discard the distant old rig's seed weights."""
import bpy,sys,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
src,out=args or [str(p/'work/rig_v1.blend'),str(p/'work/rig_weighted.blend')]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices])
J={b.name:np.array(b.head_local) for b in rig.data.bones}
for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
G={b.name:ob.vertex_groups.new(name=b.name) for b in rig.data.bones}
def sm(x,a,b):
 t=np.clip((x-a)/(b-a),0,1);return float(t*t*(3-2*t))
def mix(a,b,t):
 w={n:v*(1-t) for n,v in a.items()}
 for n,v in b.items():w[n]=w.get(n,0)+v*t
 return w
def torso(z):
 knots=[1.06,1.15,1.24,1.30];ns=['B_Pelvis','B_Spine','B_Spine1','B_Spine2']
 if z<=knots[0]:return {ns[0]:1}
 for i in range(3):
  if z<=knots[i+1]:return mix({ns[i]:1},{ns[i+1]:1},sm(z,knots[i],knots[i+1]))
 return {ns[-1]:1}
for i,(point,part) in enumerate(zip(co,pv)):
 x,y,z=point;side='L' if x>0 else 'R'
 if part in (12,13,18,100):w={'B_Pelvis':1}
 elif part in (2,7,19):w={'B_Head':1}
 elif part==1:
  w=mix(torso(z),{'B_Neck':1},sm(z,1.325,1.38))
  w=mix(w,{'B_Head':1},sm(z,1.375,1.435))
 elif part in (3,4):w={f'B_{side}_Hand':1}
 elif part in (5,6,14,15):w={f'B_{side}_Foot':1}
 elif part in (8,10):
  w=mix({f'B_{side}_Foot':1},{f'B_{side}_Calf':1},sm(z,.075,.15))
  w=mix(w,{f'B_{side}_Thigh':1},sm(z,.475,.575))
 elif part in (9,11):
  S,E,W=[J[f'B_{side}_{n}'] for n in ('UpperArm','Forearm','Hand')]
  axis=(W-S);along=(point-S)@axis/(axis@axis);et=(E-S)@axis/(axis@axis)
  w=mix({f'B_{side}_UpperArm':1},{f'B_{side}_Forearm':1},sm(along,et-.1,et+.13))
  dist=(point-W)@(W-E)/np.linalg.norm(W-E)
  w=mix(w,{f'B_{side}_Hand':1},sm(dist,-.025,.006))
 elif part==0:
  w=torso(z)
  t=sm(z,1.20,1.30)
  arm=sm(abs(x+.004),.12-.015*t,.17+.035*t)*sm(z,1.08,1.14)
  aw=mix({f'B_{side}_Clavicle':1},{f'B_{side}_UpperArm':1},sm(abs(x+.004),.12,.175))
  w=mix(w,aw,arm)
 else:raise RuntimeError(('Unmapped piece',int(part)))
 for n,v in w.items():
  if v>1e-6:G[n].add([i],float(v),'REPLACE')
# Diffuse the connected puff/torso junction, retaining the belt seam.
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==0:adj[a].append(b);adj[b].append(a)
names=list(G);W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
ids=np.flatnonzero((pv==0)&(co[:,2]>1.16)&(abs(co[:,0])>.10))
for _ in range(3):
 new=W.copy()
 for i in ids:
  if adj[i]:new[i]=.5*W[i]+.5*W[adj[i]].mean(0)
 W=new
for i in ids:
 for g in list(me.vertices[i].groups):ob.vertex_groups[g.group].remove([int(i)])
 for j in np.flatnonzero(W[i]>1e-6):ob.vertex_groups[int(j)].add([int(i)],float(W[i,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=out)
print('PFEM local region weights',len(co),'vertices')
