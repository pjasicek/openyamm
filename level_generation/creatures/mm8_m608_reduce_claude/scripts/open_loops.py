"""Open boundary loops of a mesh in a .blend: blender -b -P open_loops.py -- <blend> <object> -> loops with edge count,
centre and the dominant bone of their vertices."""
import sys, bpy, bmesh, collections
blend, name = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=blend); o = bpy.data.objects[name]
bm = bmesh.new(); bm.from_mesh(o.data); names = {g.index: g.name for g in o.vertex_groups}
edges = [e for e in bm.edges if e.is_boundary]; seen = set()
for e in edges:
    if e.index in seen: continue
    stack = [e]; loop = []
    while stack:
        x = stack.pop()
        if x.index in seen: continue
        seen.add(x.index); loop.append(x)
        for v in x.verts:
            stack += [y for y in v.link_edges if y.is_boundary and y.index not in seen]
    vs = list({v for x in loop for v in x.verts}); c = sum((v.co for v in vs[1:]), vs[0].co.copy()) / len(vs)
    bones = collections.Counter(names[g.group] for v in vs for g in o.data.vertices[v.index].groups if g.weight > .5)
    print('LOOP', len(loop), 'edges centre', tuple(round(x, 3) for x in c), bones.most_common(2))
