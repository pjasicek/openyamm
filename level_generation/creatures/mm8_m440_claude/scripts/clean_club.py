from pathlib import Path
import bpy,bmesh,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/club.blend'))
o=bpy.data.objects['ClubMesh'];bm=bmesh.new();bm.from_mesh(o.data)
bad=Vector((-.02322056144,.00601493055,.2206806093))
faces=[f for f in bm.faces if any((v.co-bad).length<1e-5 for v in f.verts) and max(v.co.z for v in f.verts)>.32]
assert len(faces)==12, len(faces)
bmesh.ops.delete(bm,geom=faces,context='FACES_ONLY')
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
assert len(o.data.polygons)==1387
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/club_clean.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/club_clean'),.385,1.2,views=('front','left','back'),resolution=(450,800))
