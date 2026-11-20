import bpy,bmesh,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
m=bpy.data.objects['Body'].data;bm=bmesh.new();bm.from_mesh(m);pv=bm.verts.layers.int['piece'];bm.verts.ensure_lookup_table()
edges=[e for e in bm.edges if e.is_boundary and all(v[pv]==1 and v.co.z>1.4 for v in e.verts)]
print('EDGES',[(e.index,[v.index for v in e.verts]) for e in edges])
for e in edges:print('EDGE',e.index,[tuple(v.co) for v in e.verts])
