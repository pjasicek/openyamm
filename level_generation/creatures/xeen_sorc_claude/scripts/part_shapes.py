"""Per-part PCA extents of work/st_v1_parts.blend (find cords/slivers). Writes work/part_shapes.json."""
import bpy, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st_v1_parts.blend'))
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    c = np.array([tuple(v.co) for v in o.data.vertices])
    m = c.mean(0); u, s, vt = np.linalg.svd(c - m, full_matrices=False)
    proj = (c - m) @ vt.T
    ext = proj.max(0) - proj.min(0)
    out[o.name] = {'ext': [round(float(x), 3) for x in ext], 'axis': [round(float(x), 2) for x in vt[0]],
                   'mean': [round(float(x), 3) for x in m], 'n': len(c)}
json.dump(out, open(os.path.join(common.WORK, 'part_shapes.json'), 'w'), indent=0)
print('SHAPES', len(out))
