from pathlib import Path
import bpy,json,numpy as np
p=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m460_claude')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
o=bpy.data.objects['Body'];co=np.array([v.co[:] for v in o.data.vertices]);pv=np.array([v.value for v in o.data.attributes['piece'].data])
rows=[]
for z0,z1 in [(0,.05),(.05,.1),(.1,.2),(.2,.5),(.5,.8)]:
 c=co[(pv==0)&(co[:,2]>=z0)&(co[:,2]<z1)];rows.append({'z':[z0,z1],'n':len(c),'lo':c.min(0).tolist() if len(c) else None,'hi':c.max(0).tolist() if len(c) else None})
print('LOWER_SKIN',json.dumps(rows),flush=True)
