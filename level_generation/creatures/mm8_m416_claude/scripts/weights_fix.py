"""m416 semantic weights: soft clothing, flexible gauntlet, separate sash folds and rigid small fittings."""
from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_raw.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
def rigid(mask,name):W[mask]=0;W[mask,gi[name]]=1
J=lambda n:np.array(rig.data.bones[n].head_local)
for side,sign in [('L',1),('R',-1)]:
 sh,cl=J(f'B_{side}_UpperArm'),J(f'B_{side}_Clavicle');axis=(sh-cl)/np.linalg.norm(sh-cl);u=gi[f'B_{side}_UpperArm'];c=gi[f'B_{side}_Clavicle'];m=pv==0;keep=np.clip(1+(co-sh)@axis/.055,0,1);move=W[:,u]*(1-keep)*m;W[:,u]-=move;W[:,c]+=move
 # Forearm pieces must not inherit the torso or opposite arm.
 m=pv==(3 if side=='L' else 4);allowed=[gi[f'B_{side}_{n}'] for n in ('UpperArm','Forearm','Hand')];other=[i for i in range(len(names)) if i not in allowed];W[np.ix_(m,other)]=0
 z=W[m].sum(1);assert z.min()>.05;W[m]/=z[:,None]
rigid(np.isin(pv,[5,9,10,16,17,18,20]),'B_Head')
rigid(np.isin(pv,[8,13]),'B_Pelvis');rigid(pv==21,'B_Spine1')
rigid(pv==11,'B_R_Calf');rigid(pv==12,'B_L_Calf')
# The neckline can bend; the face and jaw carry no shoulder weights.
m=pv==1;allowed=[gi[n] for n in ('B_Spine1','B_Spine2','B_Neck','B_Head')];other=[i for i in range(len(names)) if i not in allowed];W[np.ix_(m,other)]=0
W[m]/=np.maximum(W[m].sum(1,keepdims=True),1e-9);rigid(m&(co[:,2]>1.60),'B_Head')
for part,left_share in [(14,0.0),(15,0.0),(19,.6)]:
 m=pv==part;z=co[m,2];a=np.clip((z.max()-.025-z)/max(z.max()-.025-z.min(),1e-6),0,1)*.85
 W[m]=0;W[m,gi['B_Pelvis']]=1-a;W[m,gi['B_L_Thigh']]=a*left_share;W[m,gi['B_R_Thigh']]=a*(1-left_share)
# Continuous torso/neck weights remove nearest-transfer jumps across tiny triangles.
def vertical_weights(z, anchors):
 out=np.zeros((len(z),len(names)))
 for i,x in enumerate(z):
  if x<=anchors[0][0]:out[i,gi[anchors[0][1]]]=1;continue
  if x>=anchors[-1][0]:out[i,gi[anchors[-1][1]]]=1;continue
  for (a,na),(b,nb) in zip(anchors[:-1],anchors[1:]):
   if a<=x<=b:
    t=(x-a)/(b-a);t=t*t*(3-2*t);out[i,gi[na]]=1-t;out[i,gi[nb]]=t;break
 return out
m=pv==0;ids=np.where(m)[0];z=co[m,2]
target=vertical_weights(z,[(1.18,'B_Pelvis'),(1.29,'B_Spine'),(1.40,'B_Spine1'),(1.51,'B_Spine2')])
a=np.clip((.20-np.abs(co[m,0]))/.08,0,1)*np.clip((1.52-z)/.09,0,1);W[m]=W[m]*(1-a[:,None])+target*a[:,None]
m=pv==1;W[m]=vertical_weights(co[m,2],[(1.45,'B_Spine2'),(1.52,'B_Neck'),(1.60,'B_Head')])
# Smooth only the crotch bridge, where opposite leg weights meet on very short edges.
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==2:adj[a].append(b);adj[b].append(a)
band=(pv==2)&(co[:,2]>.90)&(co[:,2]<1.06)
for _ in range(4):
 old=W.copy()
 for i in np.where(band)[0]:
  if adj[i]:W[i]=.5*old[i]+.5*np.mean(old[adj[i]],axis=0)
assert np.isfinite(W).all() and W.sum(1).min()>.999
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i,w in enumerate(W):
 for j in np.where(w>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(w[j]),'REPLACE')
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/weighted.blend'))
(P/'work/weight_rules.json').write_text(json.dumps({'parts':json.loads((P/'work/garments.json').read_text()),'rules':'Shoulder fade, head/eyes/hair protected, cuffs on calves, belt on pelvis, sash folds one thigh mix per strip, forearm owner restriction','vertices':len(W),'all_normalized':True},indent=2))
