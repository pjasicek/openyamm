"""Open boundary loops of the Titan mesh per part (size, centre, extent). Args: blend."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, sys.argv[sys.argv.index('--') + 1]))
o = bpy.data.objects['Titan']; names = json.loads(bpy.context.scene['ttn_parts'])
part = np.zeros(len(o.data.polygons), int); o.data.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
seen = set()
for e in bm.edges:
    if not e.is_boundary or e in seen:
        continue
    loop = [e]; seen.add(e); st = [e]
    while st:
        x = st.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen:
                    seen.add(y); loop.append(y); st.append(y)
    P = np.array([tuple(v.co) for x in loop for v in x.verts])
    pn = names[part[loop[0].link_faces[0].index]]
    print('LOOP', pn, len(loop), P.mean(0).round(3).tolist(), round(float(np.ptp(P, 0).max()), 3))
