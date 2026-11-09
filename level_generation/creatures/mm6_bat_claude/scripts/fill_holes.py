import bpy, bmesh
m = bpy.data.objects['Bat']; bm = bmesh.new(); bm.from_mesh(m.data)
bnd = [e for e in bm.edges if e.is_boundary]
# group boundary edges into loops
from collections import defaultdict
adj = defaultdict(list)
for e in bnd:
    for v in e.verts: adj[v].append(e)
seen = set(); loops = []
for e in bnd:
    if e in seen: continue
    stack = [e]; comp = []
    while stack:
        x = stack.pop()
        if x in seen: continue
        seen.add(x); comp.append(x)
        for v in x.verts:
            stack += [y for y in adj[v] if y not in seen]
    loops.append(comp)
print('HOLES boundary loops', sorted(len(l) for l in loops))
n = 0
for l in loops:
    if len(l) <= 6:
        c = sum((v.co for e in l for v in e.verts), __import__('mathutils').Vector()) / (2 * len(l))
        try:
            r = bmesh.ops.edgenet_fill(bm, edges=l); n += len(r['faces'])
        except Exception as ex:
            print('HOLES fail', len(l), ex)
        print('HOLES loop', len(l), 'at', tuple(round(x, 3) for x in c))

print('HOLES filled faces', n)
bm.to_mesh(m.data); bm.free()
bpy.ops.wm.save_mainfile()
