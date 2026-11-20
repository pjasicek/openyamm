"""Remove the folded nose sliver and keep repaired UVs on adjacent painted skin."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];R=P/'review/feedback_v3'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/feedback_contacts.blend'))
o=bpy.data.objects['Body'];m=o.data;before=(len(m.vertices),len(m.polygons));changed=m.validate(verbose=True,clean_customdata=False);print('VALIDATE',changed,before,(len(m.vertices),len(m.polygons)),flush=True)
b=bmesh.new();b.from_mesh(m);pl=b.verts.layers.int['piece'];center=Vector((-.01455,-.1034,1.5181));verts=[v for v in b.verts if v[pl]==20 and (v.co-center).length<.009]
print('NOSE',len(verts),[(list(v.co),list(v.normal)) for v in verts],flush=True)
for _ in range(5):
 updates={}
 for v in verts:
  neighbours=[e.other_vert(v) for e in v.link_edges];avg=sum((x.co for x in neighbours),Vector())/len(neighbours);factor=.55*max(0,1-(v.co-center).length/.012);updates[v]=v.co.lerp(avg,factor)
 for v,co in updates.items():v.co=co
b.faces.ensure_lookup_table()
for face in list(b.faces):
 if face.index>=9896 and face.verts[0][pl]==20:
  adjacent={f for e in face.edges for f in e.link_faces if f.index<9896}
  assert adjacent
  source=max(adjacent,key=lambda f:f.calc_area())
  for uv in b.loops.layers.uv.values():
   source_uv=[Vector((l[uv].uv.x,l[uv].uv.y,0)) for l in source.loops]
   center_uv=sum(source_uv,Vector())/3
   for l,tex in zip(face.loops,source_uv):l[uv].uv=(center_uv+(tex-center_uv)*.3).xy
b.normal_update();b.to_mesh(m);b.free();m.update();assert not m.validate(verbose=True,clean_customdata=False)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/feedback_face_fixed.blend'))
(R/'face_patch.json').write_text(json.dumps({'vertices_smoothed':len(verts),'validated_geometry':True,'faces_before':before[1],'faces_after':len(m.polygons)},indent=2))
