import os, bmesh, bpy, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend = os.environ.get('REA_BLEND', 'uv_final.blend'); objn = os.environ.get('REA_OBJ', 'Wyrm')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', blend))
o = bpy.data.objects[objn]
bm = bmesh.new(); bm.from_mesh(o.data)
edges = {e for e in bm.edges if e.is_boundary}
while edges:
    e = edges.pop(); loop = [e]; fr = [e]
    while fr:
        x = fr.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in edges: edges.remove(y); loop.append(y); fr.append(y)
    c = sum((v.co for x in loop for v in x.verts), Vector()) / (2 * len(loop))
    print('LOOP', len(loop), [round(a, 3) for a in c])
