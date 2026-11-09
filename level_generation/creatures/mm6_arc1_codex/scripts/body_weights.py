"""Assign each disconnected shell to its anatomical owner before finger fitting."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_sources.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);groups={g.name:g for g in body.vertex_groups}
def assign(v,weights):
 for g in body.vertex_groups:g.remove([v.index])
 total=sum(weights.values());assert total>0
 for n,w in weights.items():
  if w>1e-5:groups[n].add([v.index],w/total,'REPLACE')
for v in me.vertices:
 part=pv[v.index];sd='L' if v.co.x>0 else 'R'
 if part in [2,3]:assign(v,{f'B_{sd}_Hand':1})
 elif part in [1,6,8,20,22,23,24] or (part==0 and v.co.z>1.445):assign(v,{'B_Head':1})
 elif part==4 or 13<=part<=19:assign(v,{'B_Spine2':1})
 elif part in [9,10,11,12]:
  e=rig.data.bones[f'B_{sd}_Forearm'].head_local;w=rig.data.bones[f'B_{sd}_Hand'].head_local;t=(v.co-e).dot(w-e)/(w-e).length_squared
  hand=max(0,min(1,(t-.87)/.13));upper=max(0,min(.5,(.1-t)/.25));assign(v,{f'B_{sd}_Hand':hand,f'B_{sd}_UpperArm':upper,f'B_{sd}_Forearm':1-hand-upper})
 elif part in [5,7,21]:
  assign(v,{f'B_{sd}_Clavicle':.55,f'B_{sd}_UpperArm':.35,'B_Spine2':.1})
 elif part==0:
  weights={body.vertex_groups[e.group].name:e.weight for e in v.groups}
  for n in list(weights):
   if any(k in n for k in ['Arm','Forearm','Hand','Clavicle']) and (v.co.z<.95 or (abs(v.co.x)<.075 and v.co.z>1.12)):
    amount=weights.pop(n);target='B_Pelvis' if v.co.z<.95 else 'B_Spine2';weights[target]=weights.get(target,0)+amount
  assign(v,weights)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_weights.blend'))
