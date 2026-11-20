"""Anatomical ownership for rigid fittings, ruff, loincloth and harness."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_fingers.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
co=np.array([tuple(v.co) for v in me.vertices]);names={g.index:g.name for g in body.vertex_groups}
original=[{names[e.group]:e.weight for e in v.groups if e.weight>1e-6} for v in me.vertices]
skin=np.where(np.isin(pv,[0,1]))[0];kd=KDTree(len(skin))
for i in skin:kd.insert(co[i],int(i))
kd.balance()
def put(i,w):
 w={k:float(v) for k,v in w.items() if v>1e-5};total=sum(w.values());assert total>0
 for g in body.vertex_groups:g.remove([int(i)])
 for n,v in w.items():(body.vertex_groups.get(n) or body.vertex_groups.new(name=n)).add([int(i)],v/total,'REPLACE')
for i,v in enumerate(me.vertices):
 p=int(pv[i]);x,y,z=co[i];side='L' if x>0 else 'R'
 if p in (0,1):continue
 if p==2:
  h=np.clip((z-1.49)/.10,0,1);n=np.clip((z-1.39)/.10,0,1)*(1-h)
  put(i,{'B_Head':h,'B_Neck':n,'B_Spine2':1-h-n})
 elif p in (20,21):put(i,{'B_Head':1})
 elif p in (7,25,26,27,28,30,31,32,35):put(i,{'B_Pelvis':1})
 elif p in (8,11):
  t=float(np.clip((1.02-z)/.28,0,.60));put(i,{'B_Pelvis':1-t,'B_L_Thigh':t*.5,'B_R_Thigh':t*.5})
 elif p in (14,15):put(i,{f'B_{side}_Thigh':1})
 elif p in (16,17,19,23):put(i,{f'B_{side}_Calf':1})
 elif p in (22,24,29,33,34):put(i,{'B_Spine2':1})
 else:
  _,si,_=kd.find(co[i]);w={n:v for n,v in original[si].items() if 'Arm' not in n and 'Clavicle' not in n and 'Hand' not in n and 'Finger' not in n}
  put(i,w or {'B_Spine2':1})
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_owned.blend'))
