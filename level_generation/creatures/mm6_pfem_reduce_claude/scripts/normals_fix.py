"""Round 2: the custom normals transferred from the master (prep_master.py) put 173 corners against their face on the
reduced mesh (fingers, ears, braid: nearest master face on a neighbouring piece); three.js shades them black (dark
spot between the clasped fingers). Keep the transferred normal only on head skin where it agrees with the face
(dot > 0.2); elsewhere the smooth vertex normal, or the face normal where even that disagrees. In place."""
import bpy, json, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
PARTS = json.loads(bpy.context.scene['pfem_parts'])
me = bpy.data.objects['Peasant'].data
part = [a.value for a in me.attributes['part'].data]; head = [a.value for a in me.attributes['head'].data]
cur = [c.vector.copy() for c in me.corner_normals]
vn = [v.normal.copy() for v in me.vertices]
out = [None] * len(me.loops); kept = fixed = 0
for p in me.polygons:
    fn = p.normal
    skin = PARTS[part[p.index]] == 'Body' and head[p.index]
    for li in p.loop_indices:
        c = cur[li]
        if skin and c.dot(fn) > 0.2:
            out[li] = c; kept += 1
        else:
            v = vn[me.loops[li].vertex_index]
            out[li] = v if v.dot(fn) > 0.0 else fn.copy()
            fixed += c.dot(fn) < 0
me.normals_split_custom_set(out)
bad = sum(1 for p in me.polygons for li in p.loop_indices if me.corner_normals[li].vector.dot(p.normal) < -0.3)
print('NORMALS kept head-skin', kept, 'replaced corners that faced away', fixed, 'remaining against face', bad)
bpy.ops.wm.save_mainfile()
