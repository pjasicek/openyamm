from pathlib import Path
import bpy,numpy as np
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
body=bpy.data.objects['Body'];me=body.data
for tag in ['cape','loin']:
 ids={i for i,v in enumerate(me.attributes[tag].data) if v.value}
 fs=[f for f in me.polygons if all(i in ids for i in f.vertices)]
 print('CLOTH_SURFACES',tag,'faces',len(fs),'normals_y',sum(f.normal.y>.3 for f in fs),sum(f.normal.y<-.3 for f in fs),'normal_z',sum(f.normal.z>.3 for f in fs),sum(f.normal.z<-.3 for f in fs),flush=True)
