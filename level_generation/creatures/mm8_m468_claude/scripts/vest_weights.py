import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_fitted.blend'));body=bpy.data.objects['Body'];me=body.data
for v,a in zip(me.vertices,me.attributes['piece'].data):
 if a.value!=1:continue
 x,y,z=v.co;cl=float(np.clip((abs(x)-.11)/.15,0,1));lower=float(np.clip((1.28-z)/.20,0,1));weights={'B_Spine1':lower*(1-cl),'B_Spine2':(1-lower)*(1-cl),('B_L_Clavicle' if x>0 else 'B_R_Clavicle'):cl}
 neck=float(np.clip((z-1.40)/.065,0,1)*np.clip((.18-abs(x))/.08,0,1));weights={n:w*(1-neck) for n,w in weights.items()};weights['B_Neck']=neck
 for g in body.vertex_groups:g.remove([v.index])
 for n,w in weights.items():
  if w>1e-5:body.vertex_groups[n].add([v.index],w,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_fitted.blend'))
