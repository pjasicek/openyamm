import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/skirt_animated.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene
names=['B_Pelvis','B_Head','B_L_Thigh','B_L_Calf','B_L_Foot','B_R_Calf','B_R_Foot','Skirt_00_0','Skirt_00_5']
P=[]
for f in range(72):
 sc.frame_set(f);P.append([r.pose.bones[n].head[:] for n in names])
P=np.array(P);acc=np.linalg.norm(P[2:]-2*P[1:-1]+P[:-2],axis=-1)
for i,n in enumerate(names):
 ix=np.argsort(acc[:,i])[-4:]+1
 print(n,'max acceleration cm',[(int(j),round(float(acc[j-1,i]*100),2)) for j in ix])
for f in range(35,46):print('POSE',f,np.round(P[f,:7],3).tolist())
