import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
root=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/remesh_01')
source=bpy.data.scenes['MM6 Goblin Restart - Remesh 01']
s=source.copy();s.name='MM6 Goblin Remesh Normals Diagnostic';bpy.context.window.scene=s
report=[]
for obj in list(s.objects):
 if obj.type!='MESH':continue
 new=obj.copy();new.data=obj.data.copy();s.collection.objects.link(new)
 for coll in list(s.collection.children):
  if obj.name in coll.objects:coll.objects.unlink(obj)
 if obj.name in s.collection.objects:s.collection.objects.unlink(obj)
 bpy.context.view_layer.objects.active=new;new.select_set(True)
 before=len(new.data.vertices)
 if new.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(new.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(new.data);bm.free()
 for face in new.data.polygons:face.use_smooth=True
 report.append({'vertices_before':before,'vertices_after':len(new.data.vertices),'triangles':sum(len(p.vertices)-2 for p in new.data.polygons)})
c=s.camera.copy();c.data=s.camera.data.copy();s.collection.objects.link(c);s.camera=c
s.render.resolution_x=800;s.render.resolution_y=900
c.location=(0,-4,0);c.rotation_euler=(Vector((0,0,0))-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=1.9963901043*1.14
s.render.filepath=str(root/'review/front_smooth_normals.png');bpy.ops.render.render(write_still=True)
s.render.resolution_y=800;target=Vector((0,-.04,.73))*1.0495647;c.location=target+Vector((0,-4,0));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=.63
s.render.filepath=str(root/'review/head_smooth_normals.png');bpy.ops.render.render(write_still=True)
(root/'normals_diagnostic.json').write_text(json.dumps(report,indent=2));print(report)
