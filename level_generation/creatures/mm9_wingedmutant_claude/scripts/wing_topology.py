"""Wing membrane topology of 'Body' in a blend: faces mostly weighted to Yw* bones, their boundary edges, and how
many face pairs sit back to back. Args: blend"""
import bpy, bmesh, sys
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
gn = {g.index: g.name for g in ob.vertex_groups}
wing = [sum(g.weight for g in v.groups if gn[g.group].startswith('Yw')) for v in ob.data.vertices]
bm = bmesh.new(); bm.from_mesh(ob.data)
wf = [f for f in bm.faces if sum(wing[v.index] for v in f.verts) / len(f.verts) > 0.5]
ws = set(wf)
bound = sum(1 for f in wf for e in f.edges if e.is_boundary)
nonman = sum(1 for f in wf for e in f.edges if not e.is_manifold)
# components of wing faces and whether each is closed
seen = set(); comps = []
for f in wf:
    if f in seen:
        continue
    st = [f]; seen.add(f); c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g in ws and g not in seen:
                    seen.add(g); st.append(g)
    comps.append(c)
info = []
for c in sorted(comps, key=len, reverse=True)[:10]:
    edges = Counter(e.index for f in c for e in f.edges)
    open_e = sum(1 for e in set(e for f in c for e in f.edges) if e.is_boundary)
    info.append((len(c), open_e))
print('WING faces', len(wf), 'boundary edge uses', bound, 'non-manifold', nonman, 'components (faces, boundary edges)', info)
