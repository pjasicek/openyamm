"""Measure the returned body's boundary and tail region before local correction."""
from pathlib import Path
import bpy, bmesh, json
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
o=bpy.data.objects['P00']
co=np.array([tuple(v.co) for v in o.data.vertices])
np.save(P/'work/body_v1_positions.npy',co)
bm=bmesh.new();bm.from_mesh(o.data)
print('BOUNDARY',[[list(v.co) for v in e.verts] for e in bm.edges if e.is_boundary])
for z in [.15,.25,.35,.45,.55,.65,.75,.85,.95,1.05,1.15]:
 a=co[(abs(co[:,2]-z)<.025)&(abs(co[:,0])<.1)]
 print('CENTRAL',z,'N',len(a),'Y',np.round(np.quantile(a[:,1],[0,.1,.25,.5,.75,.9,1]),3).tolist() if len(a) else [])
bm.free()
