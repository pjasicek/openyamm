"""Delete loose parts of 'Body' by index (numbered by lowest vertex index, as head_split.py). Args: <in> <out> <i,j,...>"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
drop = {int(x) for x in a[2].split(',')}
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = [-1] * len(bm.verts); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
dele = [v for v in bm.verts if comp[v.index] in drop]
print('DROPPARTS', sorted(drop), 'verts', len(dele))
bmesh.ops.delete(bm, geom=dele, context='VERTS'); bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
