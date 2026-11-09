import bpy,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/animations.blend'))
for name in ['Body','Head']:
 bm=bmesh.new();bm.from_mesh(bpy.data.objects[name].data);edges=[e for e in bm.edges if e.is_boundary];print('BEFORE',name,len(edges));print('EDGECO',[(tuple(e.verts[0].co),tuple(e.verts[1].co)) for e in edges]);r=bmesh.ops.holes_fill(bm,edges=edges,sides=0);print('FILLED',len(r['faces']));print('AFTER',[(tuple(e.verts[0].co),tuple(e.verts[1].co)) for e in bm.edges if e.is_boundary])
