"""Close the generated skirt puncture, tuck the neckline, and remove hidden thighs."""
import bpy,bmesh,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/reduced.blend'));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bm=bmesh.new();bm.from_mesh(o.data);piece=bm.verts.layers.int['piece']
es=[e for e in bm.edges if e.is_boundary and all(v[piece]==100 and .25<v.co.z<.95 for v in e.verts)]
filled=bmesh.ops.holes_fill(bm,edges=es,sides=12)['faces']
for f in filled:f.smooth=True
print('CLOSED skirt punctures',len(filled))
# The chosen clips keep these surfaces inside the long skirt in every view.
hidden=[v for v in bm.verts if v[piece] in (8,10) and v.co.z>.425]
bmesh.ops.delete(bm,geom=hidden,context='VERTS')
legends=[e for e in bm.edges if e.is_boundary and all(v[piece] in (8,10) and v.co.z>.30 for v in e.verts)]
caps=bmesh.ops.holes_fill(bm,edges=legends,sides=100)['faces']
# Skin and neckline were coincident. Extend the skin just under the garment.
edges=[e for e in bm.edges if e.is_boundary and all(v[piece]==1 for v in e.verts)]
res=bmesh.ops.extrude_edge_only(bm,edges=edges)
newverts=[v for v in res['geom'] if isinstance(v,bmesh.types.BMVert)]
for v in newverts:v.co.z-=.012
for f in bm.faces:f.smooth=True
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(o.data);bm.free();o.data.update()
o.data.validate(clean_customdata=False)
print('FINAL MESH',len(o.data.vertices),len(o.data.polygons),'hidden leg vertices removed',len(hidden))
assert len(o.data.polygons)<=10000
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/reduced.blend'))
