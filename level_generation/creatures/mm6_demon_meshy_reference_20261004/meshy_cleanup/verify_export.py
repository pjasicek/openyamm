import bpy
import bmesh
import hashlib
import json
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_cleanup')
cleanup_scene = bpy.data.scenes['MM6_Demon_Cleanup']
cleaned = cleanup_scene.objects['Demon_Cleaned']
scenes_before = set(bpy.data.scenes.keys())
scene = bpy.data.scenes.new('MM6_Demon_Export_Verification')
bpy.context.window.scene = scene
bpy.ops.import_scene.gltf(filepath=str(stage / 'mm6_demon_cleaned.glb'))
objects = [obj for obj in scene.objects if obj.type == 'MESH']
assert len(objects) == 1 and len(scene.objects) == 1
obj = objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)
original_coordinates = sorted(tuple(cleaned.matrix_world @ vertex.co) for vertex in cleaned.data.vertices)
export_coordinates = sorted(tuple(obj.matrix_world @ vertex.co) for vertex in obj.data.vertices)
assert len(original_coordinates) == len(export_coordinates)
coordinate_error = max((Vector(a) - Vector(b)).length
                       for a, b in zip(original_coordinates, export_coordinates))
report = {
    'reimported_mesh_objects': len(objects), 'reimported_total_objects': len(scene.objects),
    'vertices': len(obj.data.vertices), 'triangles': len(obj.data.polygons),
    'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
    'nonmanifold_edges': sum(not edge.is_manifold for edge in bm.edges),
    'nonmanifold_vertices': sum(not vertex.is_manifold for vertex in bm.verts),
    'inconsistent_winding_edges': sum(not edge.is_contiguous for edge in bm.edges),
    'zero_area_faces': sum(face.calc_area() < 1e-12 for face in bm.faces),
    'maximum_coordinate_error': coordinate_error,
    'existing_scenes_preserved': scenes_before.issubset(set(bpy.data.scenes.keys())),
    'source_sha256_unchanged': hashlib.sha256(Path(cleaned['source_file']).read_bytes()).hexdigest()
                              == 'fe573922ad435c24c605e1d7f3edad8788606f15204e0447f4a47463b6f70d90',
}
bm.free()
assert report['vertices'] == 7899 and report['triangles'] == 15686
assert coordinate_error < 1e-7
assert all(report[key] == 0 for key in ('boundary_edges', 'nonmanifold_edges',
    'nonmanifold_vertices', 'inconsistent_winding_edges', 'zero_area_faces'))
assert report['existing_scenes_preserved'] and report['source_sha256_unchanged']
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = cleanup_scene.world
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.62, .66, .7)
scene.display.shading.studiolight_rotate_z = .4
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
camera = cleanup_scene.camera.copy()
camera.data = cleanup_scene.camera.data.copy()
scene.collection.objects.link(camera)
scene.camera = camera
scene.render.filepath = str(stage / 'export_reimport_preview.png')
bpy.ops.render.render(write_still=True)
(stage / 'export_verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
bpy.context.window.scene = cleanup_scene
for item in cleanup_scene.objects:
    item.select_set(False)
cleaned.select_set(True)
bpy.context.view_layer.objects.active = cleaned
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.shading.type = 'SOLID'
        space.shading.show_shadows = False
        space.shading.color_type = 'SINGLE'
        space.shading.single_color = (.62, .66, .7)
        space.overlay.show_overlays = False
        space.region_3d.view_location = Vector((0, 0, 0))
        space.region_3d.view_rotation = cleanup_scene.camera.rotation_euler.to_quaternion()
        space.region_3d.view_distance = 1.7
        space.region_3d.view_perspective = 'ORTHO'
