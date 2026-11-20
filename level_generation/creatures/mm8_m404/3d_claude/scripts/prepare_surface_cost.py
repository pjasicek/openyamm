import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_weighted_final.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
names=[g.name for g in o.vertex_groups];w=np.zeros((len(o.data.vertices),len(names)))
for v in o.data.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
for i,n in enumerate(names):
 if 'Twist' in n:w[:,names.index(n.replace('Twist',''))]+=w[:,i];w[:,i]=0
np.savez(p/'work/surface_cost.npz',co=np.array([v.co[:] for v in o.data.vertices]),weights=w,names=names,edges=np.array([e.vertices[:] for e in o.data.edges]),piece=np.array([v.value for v in o.data.attributes['piece'].data]))
