"""List the Body mesh's loose parts (numbered by lowest vertex index, as head_split.py) with face counts, head/hand
attribute share, material and rest bounding box (Blender coordinates, metres). Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
for o in bpy.data.objects:
    print('OBJ', o.name, o.type, o.parent.name if o.parent else None, len(o.data.vertices) if o.type == 'MESH' else '')
body = bpy.data.objects['Body']; me = body.data
print('ATTRS', [(a.name, a.domain, a.data_type) for a in me.attributes])
print('UV', [u.name for u in me.uv_layers], 'MATS', [m.name if m else None for m in me.materials])
print('VGROUPS', len(body.vertex_groups))
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
co = np.array([v.co[:] for v in bm.verts])
n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
if 'head' in me.attributes: me.attributes['head'].data.foreach_get('value', hd)
if 'hand' in me.attributes: me.attributes['hand'].data.foreach_get('value', hn)
fpart = np.array([comp[p.vertices[0]] for p in me.polygons])
for c in range(cid):
    vs = comp == c; fs = fpart == c
    lo = co[vs].min(0); hi = co[vs].max(0)
    print(f'PART {c:3d} v {vs.sum():5d} f {fs.sum():5d} head {hd[fs].mean() if fs.any() else 0:.2f} hand {hn[fs].mean() if fs.any() else 0:.2f} '
          f'lo {np.round(lo,3).tolist()} hi {np.round(hi,3).tolist()}')
