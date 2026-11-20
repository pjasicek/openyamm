import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
me=bpy.data.objects['Body'].data
co=np.array([tuple(v.co)for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data])
off=json.loads((P/'work/skull_fit.json').read_text())['offset']
for s in [-1,1]:
    c=np.array([off[0]+s*.027,1.675]);r=np.linalg.norm(co[:,[0,2]]-c,axis=1)
    for a,b in [(0,.004),(.004,.008),(.008,.012),(.012,.016)]:
        pts=co[(piece==2000)&(r>=a)&(r<b)]
        print('EYE',s,a,b,len(pts),'y',np.quantile(pts[:,1],[0,.1,.25,.5,.75,.9,1]).tolist())
