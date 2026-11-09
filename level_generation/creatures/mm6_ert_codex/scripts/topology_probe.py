import bpy,bmesh,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
bm=bmesh.new();bm.from_mesh(bpy.data.objects['Body'].data)
print('EDGES',collections.Counter(len(e.link_faces) for e in bm.edges))
print('BOUNDARY DEGREE',collections.Counter(sum(e.is_boundary for e in v.link_edges) for v in bm.verts if v.is_boundary))
for v in bm.verts:
 if sum(e.is_boundary for e in v.link_edges)>2: print('JUNCTION',v.index,tuple(v.co),sum(e.is_boundary for e in v.link_edges))
for e in bm.edges:
 if len(e.link_faces)>2: print('OVERFULL',tuple(e.verts[0].co),tuple(e.verts[1].co),[(f.index,f.calc_area(),tuple(f.normal)) for f in e.link_faces])
