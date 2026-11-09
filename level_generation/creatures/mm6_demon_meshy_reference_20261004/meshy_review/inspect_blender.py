import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_review')
source = '/home/pjasicek/Downloads/Meshy_AI_Spineclaw_Warlord_1004160609_generate.glb'
original_scene = bpy.context.scene
scene = bpy.data.scenes.new('MM6_Demon_Meshy_Review')
bpy.context.window.scene = scene
bpy.ops.import_scene.gltf(filepath=source)
meshes = [obj for obj in scene.objects if obj.type == 'MESH']
assert len(meshes) == 1
obj = meshes[0]
obj.name = 'Demon_Meshy_Original'
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)
report = {
    'blender_version': bpy.app.version_string,
    'inspection_transport': 'Blender MCP add-on socket commands',
    'original_scene_preserved': original_scene.name,
    'review_scene': scene.name,
    'vertices': len(mesh.vertices),
    'faces': len(mesh.polygons),
    'uv_layers': len(mesh.uv_layers),
    'materials': len(mesh.materials),
    'armature_objects': sum(item.type == 'ARMATURE' for item in scene.objects),
    'animations': bool(obj.animation_data),
    'dimensions': list(obj.dimensions),
    'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
    'nonmanifold_edges': sum(not edge.is_manifold for edge in bm.edges),
    'loose_edges': sum(edge.is_wire for edge in bm.edges),
}
bm.free()
(stage / 'blender_audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))

bpy.context.view_layer.objects.active = obj
obj.select_set(True)
for polygon in mesh.polygons:
    polygon.use_smooth = True

corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
low = Vector([min(point[i] for point in corners) for i in range(3)])
high = Vector([max(point[i] for point in corners) for i in range(3)])
center = (low + high) / 2
extent = max(high - low)
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.display.shading.light = 'STUDIO'
scene.display.shading.studiolight_rotate_z = 0.4
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.62, 0.66, 0.7)
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('DemonReviewWorld')
scene.world.color = (0.065, 0.075, 0.09)

camera_data = bpy.data.cameras.new('DemonReviewCamera')
camera = bpy.data.objects.new('DemonReviewCamera', camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'
camera_data.ortho_scale = extent * 1.25
scene.camera = camera
views = [('front', (0, -3, 0.12)), ('three_quarter', (1.7, -3, 0.32)),
         ('side', (3, 0, 0.12)), ('back', (0, 3, 0.12))]
for name, direction in views:
    camera.location = center + Vector(direction) * extent
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)
    print('Rendered', name)

audit = json.loads((stage / 'geometry_audit.json').read_text())
material = bpy.data.materials.new('SuspiciousLongSlivers')
material.diffuse_color = (0.9, 0.04, 0.02, 1)
mesh.materials.append(material)
for index in audit['sliver_indices']:
    mesh.polygons[index].material_index = len(mesh.materials) - 1
scene.display.shading.color_type = 'MATERIAL'
base_material = bpy.data.materials.new('ReviewNeutral')
base_material.diffuse_color = (0.62, 0.66, 0.7, 1)
mesh.materials.append(base_material)
for polygon in mesh.polygons:
    if polygon.index not in audit['sliver_indices']:
        polygon.material_index = len(mesh.materials) - 1
camera.location = center + Vector((0, -3, 0.12)) * extent
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.render.filepath = str(stage / 'front_slivers.png')
bpy.ops.render.render(write_still=True)
print('Rendered highlighted slivers')

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.shading.type = 'SOLID'
        space.shading.color_type = 'MATERIAL'
        space.overlay.show_floor = False
        space.overlay.show_axis_x = False
        space.overlay.show_axis_y = False
        space.region_3d.view_location = center
        space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
        space.region_3d.view_distance = extent * 1.7
        space.region_3d.view_perspective = 'ORTHO'
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'demon_inspection.blend'), copy=True)
print('Review copy saved; original GLB and default scene preserved')
