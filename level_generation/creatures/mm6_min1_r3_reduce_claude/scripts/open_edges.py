"""Open-edge loops of the source and every ladder candidate (work/ladder.blend): count, edges, and the loops a
candidate has that the source does not (centre, size). Usage: blender -b -P open_edges.py"""
import os, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))


def loops(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    edges = [e for e in bm.edges if e.is_boundary]; seen = set(); out = []
    for e in edges:
        if e in seen: continue
        stack = [e]; comp = []
        while stack:
            x = stack.pop()
            if x in seen: continue
            seen.add(x); comp.append(x)
            for v in x.verts:
                stack.extend(y for y in v.link_edges if y.is_boundary and y not in seen)
        c = sum((v.co for x in comp for v in x.verts), Vector()) / (2 * len(comp))
        out.append((len(comp), c.copy()))
    bm.free(); return out


src = loops(bpy.data.objects['Body'])
print('SOURCE loops', len(src), 'edges', sum(n for n, _ in src))
for o in sorted((o for o in bpy.data.objects if o.name.startswith('Cand_')), key=lambda o: o.name):
    ls = loops(o)
    new = [(n, c) for n, c in ls if min((c - sc).length for _, sc in src) > 0.02]
    print(o.name, 'loops', len(ls), 'edges', sum(n for n, _ in ls), 'new', len(new),
          ' '.join(f'{n}@({c.x:.2f},{c.y:.2f},{c.z:.2f})' for n, c in sorted(new, key=lambda x: -x[0])[:6]))
