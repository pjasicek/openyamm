"""Remove the residual Meshy head turn from the lower jaw while preserving the paid UV layout and clips."""
import bpy
import math
import json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix

PROJECT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/wolf_uv_master.blend'))
mesh=bpy.data.objects['Wolf'];pivot=Vector((.02,-.30,.32));angle=math.radians(-35)
def weight(co,new=False):
    value=min(1.,max(0.,(-co.y-.29)/.075))
    value*=min(1.,max(0.,(co.z-(.10 if new else .18))/(.045 if new else .055)))
    return value*value*(3-2*value)
before=np.array([v.co[:] for v in mesh.data.vertices]);changed=[];inverse_error=[]
for v in mesh.data.vertices:
    if v.co.y>=-.36 or v.co.z>=.235 or v.co.z<=.1:continue
    current=v.co.copy();original=current.copy()
    for _ in range(60):original=pivot+Matrix.Rotation(-angle*weight(original),3,'Z')@(current-pivot)
    check=pivot+Matrix.Rotation(angle*weight(original),3,'Z')@(original-pivot)
    inverse_error.append((check-current).length)
    v.co=pivot+Matrix.Rotation(angle*weight(original,True),3,'Z')@(original-pivot)
    changed.append(v.index)
assert max(inverse_error)<1e-5
after=np.array([v.co[:] for v in mesh.data.vertices])
report={'changed_vertices':len(changed),'max_inverse_error':max(inverse_error),
        'max_displacement_m':float(np.linalg.norm(after-before,axis=1).max()),
        'uvs_weights_clips':'unchanged','cause':'Original head-turn correction feathered through the lower jaw vertically'}
(PROJECT/'work/jaw_repair.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'work/wolf_uv_repaired.blend'))
print(json.dumps(report),flush=True)
