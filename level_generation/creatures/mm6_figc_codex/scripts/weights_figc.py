import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v2t.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data
names=[g.name for g in ob.vertex_groups];gi={n:i for i,n in enumerate(names)};W=np.zeros((len(me.vertices),len(names)));pv=np.array([x.value for x in me.attributes['piece'].data]);co=np.array([tuple(v.co) for v in me.vertices])
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
J=lambda n:np.array(rig.data.bones[n].head_local)
def assign(mask,weights):
 ids=np.where(mask)[0];W[ids]=0
 for n,w in weights.items():W[ids,gi[n]]=w
rigid={1:'B_L_Hand',2:'B_R_Hand',3:'B_Head',6:'B_Pelvis',7:'B_R_Clavicle',8:'B_L_Clavicle',9:'B_Pelvis',10:'B_Head',11:'B_Head',12:'B_R_ForearmTwist',13:'B_Spine2',14:'B_Pelvis',15:'B_Head',16:'B_Head',17:'B_R_Calf',18:'B_L_Calf',19:'B_L_Calf',20:'B_R_Calf',21:'B_L_Thigh',22:'B_R_Thigh',23:'B_Pelvis',24:'B_R_Calf',25:'B_L_Calf',26:'B_R_Calf',27:'B_L_Calf',28:'B_L_Calf',29:'B_R_Calf',30:'B_L_Foot',31:'B_L_Foot',32:'B_R_Foot',33:'B_R_Calf',34:'B_R_Foot',35:'B_L_Calf',36:'B_R_Calf',37:'B_L_Calf',38:'B_Pelvis',39:'B_Pelvis'}
for part,n in rigid.items():assign(pv==part,{n:1})
# This mesh's left sleeve and bracer are one component: the metal starts below the elbow.
left=J('B_L_Forearm');wrist=J('B_L_Hand');axis=wrist-left;t=(co-left)@axis/(axis@axis);assign((pv==4)&(t>.16),{'B_L_ForearmTwist':1})
# Sleeve surfaces use an anatomical shoulder/elbow/wrist blend, with no torso bleed.
for side, part in [('L',4),('R',5)]:
 shoulder=J(f'B_{side}_UpperArm');elbow=J(f'B_{side}_Forearm');wrist=J(f'B_{side}_Hand')
 axis=elbow-shoulder;t=(co-shoulder)@axis/(axis@axis)
 ids=np.where((pv==part)&((co-elbow)@(wrist-elbow)/((wrist-elbow)@(wrist-elbow))<=.16 if side=='L' else pv==part))[0]
 u=np.clip((t[ids]-.78)/.40,0,1);u=u*u*(3-2*u)
 counter=np.clip(1-t[ids]/.7,0,1)
 W[ids]=0;W[ids,gi[f'B_{side}_UpperArmTwist']]=(1-u)*counter
 W[ids,gi[f'B_{side}_UpperArm']]=(1-u)*(1-counter)
 W[ids,gi[f'B_{side}_ForearmTwist']]=u
# The torso/tabard/legs share a shell; remove arm bleed from chest and head without touching sleeves.
arm=[gi[n] for n in names if any(k in n for k in ['UpperArm','Forearm','Hand','Finger'])]
ids=np.where((pv==0)&(co[:,2]>1.03))[0];removed=W[np.ix_(ids,arm)].sum(1);W[np.ix_(ids,arm)]=0;W[ids,gi['B_Spine2']]+=removed
assign((pv==0)&(co[:,2]>1.48),{'B_Head':1})
# Preserve a smooth neck transition under the helmet.
ids=np.where((pv==0)&(co[:,2]>1.40)&(co[:,2]<=1.48))[0];u=np.clip((co[ids,2]-1.40)/.08,0,1);W[ids]=0;W[ids,gi['B_Neck']]=1-u;W[ids,gi['B_Head']]=u
# Metal feet do not bend at the toes.
for side in ['L','R']:
 a,b=gi[f'B_{side}_Toe0'],gi[f'B_{side}_Foot'];W[:,b]+=W[:,a];W[:,a]=0
W/=np.maximum(W.sum(1,keepdims=True),1e-9);assert np.allclose(W.sum(1),1,atol=1e-4)
for g in list(ob.vertex_groups):ob.vertex_groups.remove(g)
for n in names:ob.vertex_groups.new(name=n)
for i in range(len(W)):
 for j in np.where(W[i]>1e-5)[0]:ob.vertex_groups[j].add([i],float(W[i,j]),'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v3.blend'));print('WEIGHTS_FIGC',len(W),'vertices',flush=True)
