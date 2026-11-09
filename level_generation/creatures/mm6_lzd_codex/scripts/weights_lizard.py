"""Keep rigid equipment on its owner and remove auto-rig shoulder/tail bleed."""
import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v4.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
pv=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
original=W.copy()
def rigid(parts,weights):
 ids=np.where(np.isin(pv,parts))[0];W[ids]=0
 for n,w in weights.items():W[ids,gi[n]]=w
rigid([6,11,29,30,31,32,33,34,35,36,60,96,99,100,101,102,103,104,105],{'B_Spine2':1})
rigid([10,12,23],{'B_Pelvis':1})
for side,br,plate,greaves in [('R',[7,45],[16],[13,19,21,26,27,43,47,53,55]),('L',[8,49],[17],[14,20,22,25,28,44,46,52,57])]:
 rigid(br,{f'B_{side}_ForearmTwist':1})
 rigid(plate,{f'B_{side}_Clavicle':.7,f'B_{side}_UpperArm':.3})
 rigid(greaves,{f'B_{side}_Calf':1})
# Weight arm skin by the fitted hinges; auto-rig retained sharp elbow/upper-arm boundaries.
for sd,piece in [('L',3),('R',4)]:
 J=lambda n:np.array(rig.data.bones[f'B_{sd}_{n}'].head_local)
 sh,el,wr=J('UpperArm'),J('Forearm'),J('Hand');axis=(wr-sh);axis/=np.linalg.norm(axis);fa=(wr-el);fl=np.linalg.norm(fa);fa/=fl
 for i in np.where(pv==piece)[0]:
  if sum(W[i,k]for n,k in gi.items()if 'Finger'in n)>.001:continue
  elbow=float(np.clip(((co[i]-el)@axis+.055)/.11,0,1));hand=float(np.clip(((co[i]-wr)@fa+.025)/.06,0,1));W[i]=0
  W[i,gi[f'B_{sd}_UpperArm']]=(1-elbow)*(1-hand)
  W[i,gi[f'B_{sd}_ForearmTwist']]=elbow*(1-hand)
  W[i,gi[f'B_{sd}_Hand']]=hand
# Smooth sleeve-to-chest blend; hard x cutoffs tore the tunic at the shoulder.
for i in np.where(np.isin(pv,[2,9]))[0]:
 sd='L'if co[i,0]>0 else'R';u=float(np.clip((abs(co[i,0])-.08)/.25,0,1))
 if pv[i]==9:u=0
 W[i]=0;W[i,gi['B_Spine2']]=1-u;W[i,gi[f'B_{sd}_UpperArm']]=u
# Broad face is rigid; the neck root blends into the chest under the collar.
ids=np.where(pv==200)[0];W[ids]=0
for i in ids:
 t=float(np.clip((co[i,2]-1.345)/.085,0,1));W[i,gi['B_Head']]=t;W[i,gi['B_Neck']]=1-t
# Uniform left/right mix across each flap avoids splitting its middle with the legs.
ids=np.where(pv==15)[0];W[ids]=0
for i in ids:
 t=float(np.clip((1.0-co[i,2])/.27,0,1))*.5;W[i,gi['B_Pelvis']]=1-t;W[i,gi['B_L_Thigh']]=t*.5;W[i,gi['B_R_Thigh']]=t*.5
# Tail is a pelvis appendage until its three local bones are added after retargeting.
ids=np.where((pv==1)&(co[:,1]>.15))[0];W[ids]=0;W[ids,gi['B_Pelvis']]=1
W/=np.maximum(W.sum(1,keepdims=True),1e-9)
assert np.all(np.isfinite(W)) and np.allclose(W.sum(1),1),np.where(W.sum(1)<.9)
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i in range(len(co)):
 for j in np.where(W[i]>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(W[i,j]),'REPLACE')
(P/'work/weights_report.json').write_text(json.dumps({'changed_vertices':int(np.any(abs(W-original)>.001,axis=1).sum()),'vertices':len(co)},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v5.blend'))
