import bpy
import bmesh
import json
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_cleanup')
geometry = json.loads((stage / 'repaired_geometry.json').read_text())
scene = bpy.data.scenes.get('MM6_Demon_Cleanup')
if scene is None:
    scene = bpy.data.scenes.new('MM6_Demon_Cleanup')
bpy.context.window.scene = scene
old = bpy.data.objects.get('Demon_Cleaned')
if old:
    bpy.data.objects.remove(old, do_unlink=True)
mesh = bpy.data.meshes.new('Demon_LocalRepair')
mesh.from_pydata([(x, -z, y) for x, y, z in geometry['vertices_gltf']], [], geometry['faces'])
mesh.update()
obj = bpy.data.objects.new('Demon_Cleaned', mesh)
scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
for polygon in mesh.polygons:
    polygon.use_smooth = True

scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.studiolight_rotate_z = .4
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'
scene.display.shading.background_type = 'WORLD'
scene.world = bpy.data.worlds.new('DemonCleanupWorld')
scene.world.color = (.065, .075, .09)
material = bpy.data.materials.new('Demon_Neutral_Inspection')
material.diffuse_color = (.62, .66, .7, 1)
mesh.materials.append(material)
camera_data = bpy.data.cameras.new('DemonCleanupCamera')
camera = bpy.data.objects.new('DemonCleanupCamera', camera_data)
scene.collection.objects.link(camera)
camera_data.type = 'ORTHO'
scene.camera = camera

def render(name, direction, center=(0, 0, 0), scale=1.25):
    center = Vector(center)
    camera_data.ortho_scale = scale
    camera.location = center + Vector(direction) * 1.5
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)
    print('Rendered', name)

render('repair_front', (0, -3, .12))
render('repair_three_quarter', (1.7, -3, .32))
render('repair_side', (3, 0, .12))
render('repair_back', (0, 3, .12))
render('repair_head_chest', (0, -3, .05), (0, -.08, .3), .48)
render('repair_legs', (1, -3, .05), (0, -.12, -.33), .48)

# Separate diagnostic curves, never included in the portable model.
bm = bmesh.new()
bm.from_mesh(mesh)
curve = bpy.data.curves.new('OpenBoundaryDiagnostic', 'CURVE')
curve.dimensions = '3D'
curve.bevel_depth = .0008
curve.bevel_resolution = 0
for edge in bm.edges:
    if edge.is_boundary:
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        for point, vertex in zip(spline.points, edge.verts):
            point.co = (*vertex.co, 1)
bm.free()
boundary_obj = bpy.data.objects.new('Boundary_Diagnostic', curve)
scene.collection.objects.link(boundary_obj)
boundary_material = bpy.data.materials.new('BoundaryOrange')
boundary_material.diffuse_color = (1, .08, .015, 1)
curve.materials.append(boundary_material)
render('boundaries_front', (0, -3, .05), (0, -.09, .3), .48)
render('boundaries_back', (0, 3, .05), (0, -.09, .3), .48)
boundary_obj.hide_render = True
boundary_obj.hide_set(True)
render('repair_final_view', (1.7, -3, .32))
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.shading.type = 'SOLID'
        space.overlay.show_overlays = False
        space.region_3d.view_location = Vector((0, 0, 0))
        space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
        space.region_3d.view_distance = 1.7
        space.region_3d.view_perspective = 'ORTHO'
print('Local repair available in', scene.name)
