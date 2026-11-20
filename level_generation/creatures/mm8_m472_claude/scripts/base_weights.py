from pathlib import Path
import bpy,sys,runpy
import numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v1.blend'))
o=bpy.data.objects['Body'];me=o.data;pv=me.attributes['piece'].data
for v in me.vertices:
 piece=pv[v.index].value
 if piece in (3,4):w={'B_L_Hand' if piece==3 else 'B_R_Hand':1}
 elif piece in (2,8,9,10,11):
  t=float(np.clip((v.co.z-1.43)/.08,0,1));w={'B_Neck':1-t,'B_Head':t}
 elif piece==1:w={'B_Head':1}
 elif piece in (5,6,7):w={'B_Pelvis':1}
 else:
  w={}
  for g in v.groups:
   name=o.vertex_groups[g.group].name
   if 'Hand' in name or 'Finger' in name:name='B_'+('L' if v.co.x>0 else 'R')+'_Forearm'
   w[name]=w.get(name,0)+g.weight
 for g in o.vertex_groups:g.remove([v.index])
 total=sum(w.values());assert total>0
 for n,x in w.items():
  if x>1e-5:o.vertex_groups[n].add([v.index],x/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_owned.blend'))
s=p/'scripts/finger_weights.py';sys.argv=[str(s),'--',str(p/'work/rig_owned.blend'),str(p/'work/rig_fingers.blend')];runpy.run_path(str(s),run_name='__main__')
