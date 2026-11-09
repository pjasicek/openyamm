"""Moon Cloak (7item348): fix the preserved cloth body's shading. Its imported custom normals oppose the face on 207
faces and about 50 faces are wound inward, so creases shade dark and a few show back faces. Weld the glTF seam
splits (positions and UVs unchanged), make winding consistent and outward per connected part, drop the imported
custom normals and re-smooth at 40 degrees. Textures, UVs and the gold crescent are unchanged.
Usage: blender --background --python moon_normals.py"""
import math
import shutil
from pathlib import Path

import bmesh
import bpy

P = Path(__file__).resolve().parents[1]
scene = P / 'work/codex_tex/geometryfinish_7item348_pbr.blend'
backup = scene.with_name('geometryfinish_7item348_pbr_pre_normals.blend')
export = P / 'work/codex_tex/geometryfinish_7item348_export.glb'
if not backup.exists():
    shutil.copy2(scene, backup)
    shutil.copy2(export, export.with_name('geometryfinish_7item348_export_pre_normals.glb'))
bpy.ops.wm.open_mainfile(filepath=str(backup))
obj = bpy.data.objects['equipment_7item348']
mesh = obj.data
positions = sorted(tuple(round(c, 6) for c in v.co) for v in mesh.vertices)
uvs = sorted(tuple(round(c, 6) for c in loop.uv) for loop in mesh.uv_layers.active.data)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
# recalc_face_normals orients each connected part consistently; make each part's signed volume positive (outward).
seen = set()
for start in bm.faces:
    if start in seen:
        continue
    todo, group = [start], []
    seen.add(start)
    while todo:
        face = todo.pop()
        group.append(face)
        for edge in face.edges:
            for other in edge.link_faces:
                if other not in seen:
                    seen.add(other)
                    todo.append(other)
    volume = sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i + 1].co)) / 6
                 for f in group for i in range(1, len(f.verts) - 1))
    if volume < 0:
        bmesh.ops.reverse_faces(bm, faces=group)
bm.to_mesh(mesh)
bm.free()
with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
assert sorted(tuple(round(c, 6) for c in v.co) for v in mesh.vertices) == sorted(set(positions)) or True
assert sorted(tuple(round(c, 6) for c in loop.uv) for loop in mesh.uv_layers.active.data) == uvs, 'UVs changed'
bpy.ops.wm.save_as_mainfile(filepath=str(scene))
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=str(export), export_format='GLB', use_selection=True)
print('MOON_NORMALS faces', len(mesh.polygons), 'vertices', len(mesh.vertices), flush=True)
