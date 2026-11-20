"""List faces of 'Body' within R of a point, with their component size. Args: <blend> x y z r"""
import bpy, bmesh, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
P = Vector([float(x) for x in argv[1:4]]); R = float(argv[4])
ob = bpy.data.objects['Body']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
comp_of = {}
cid = 0
for v in bm.verts:
    if v.index in comp_of:
        continue
    st = [v]; comp_of[v.index] = cid; n = 0
    while st:
        x = st.pop(); n += 1
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in comp_of:
                comp_of[y.index] = cid; st.append(y)
    cid += 1
sizes = {}
for k in comp_of.values():
    sizes[k] = sizes.get(k, 0) + 1
for f in bm.faces:
    c = f.calc_center_median()
    if (c - P).length < R:
        print('NEAR face', f.index, [round(x, 3) for x in c], 'comp', comp_of[f.verts[0].index], 'size', sizes[comp_of[f.verts[0].index]], 'area %.6f' % f.calc_area())
