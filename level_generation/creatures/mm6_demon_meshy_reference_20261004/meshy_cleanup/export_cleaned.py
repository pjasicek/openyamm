import bpy
import bmesh
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from mathutils import Vector

stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/meshy_cleanup')
source = Path('/home/pjasicek/Downloads/Meshy_AI_Spineclaw_Warlord_1004160609_generate.glb')
geometry = json.loads((stage / 'final_geometry.json').read_text())
scene = bpy.data.scenes['MM6_Demon_Cleanup']
bpy.context.window.scene = scene
obj = scene.objects['Demon_Cleaned']
old_mesh = obj.data
mesh = bpy.data.meshes.new('Demon_Cleaned_Geometry')
mesh.from_pydata([(x, -z, y) for x, y, z in geometry['vertices_gltf']], [], geometry['faces'])
mesh.update()
obj.data = mesh
if old_mesh.users == 0:
    bpy.data.meshes.remove(old_mesh)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
remaining = set(bm.faces)
components = []
while remaining:
    group = set()
    queue = [next(iter(remaining))]
    while queue:
        face = queue.pop()
        if face in group:
            continue
        group.add(face)
        for edge in face.edges:
            queue.extend(neighbor for neighbor in edge.link_faces if neighbor not in group)
    remaining -= group
    volume = sum(face.verts[0].co.dot(face.verts[1].co.cross(face.verts[2].co)) / 6
                 for face in group)
    if volume < 0:
        bmesh.ops.reverse_faces(bm, faces=list(group))
        volume = -volume
    components.append({'triangles': len(group), 'signed_volume': volume})
report = {
    'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'blender': bpy.app.version_string,
    'vertices': len(bm.verts), 'triangles': len(bm.faces),
    'boundary_edges': sum(edge.is_boundary for edge in bm.edges),
    'nonmanifold_edges': sum(not edge.is_manifold for edge in bm.edges),
    'nonmanifold_vertices': sum(not vertex.is_manifold for vertex in bm.verts),
    'inconsistent_winding_edges': sum(not edge.is_contiguous for edge in bm.edges),
    'loose_edges': sum(edge.is_wire for edge in bm.edges),
    'loose_vertices': sum(not vertex.link_faces for vertex in bm.verts),
    'zero_area_faces': sum(face.calc_area() < 1e-12 for face in bm.faces),
    'closed_surface_components': sorted(components, key=lambda item: -item['triangles']),
}
assert report['source_sha256'] == 'fe573922ad435c24c605e1d7f3edad8788606f15204e0447f4a47463b6f70d90'
assert all(report[key] == 0 for key in (
    'boundary_edges', 'nonmanifold_edges', 'nonmanifold_vertices',
    'inconsistent_winding_edges', 'loose_edges', 'loose_vertices', 'zero_area_faces'
)), report
assert all(component['signed_volume'] > 0 for component in components)
bm.to_mesh(mesh)
bm.free()
mesh.update()
for polygon in mesh.polygons:
    polygon.use_smooth = True
obj['source_file'] = str(source)
obj['cleanup'] = 'Local displaced cap/helper repair; annular and shell seam closure; consistent outward normals'
obj['not_yet_authored'] = 'UVs, reference textures, armature, skin weights, animations'
material = bpy.data.materials.get('Demon_Neutral_Inspection')
mesh.materials.append(material)
for item in list(scene.objects):
    if item.name.startswith('Boundary_Diagnostic'):
        bpy.data.objects.remove(item, do_unlink=True)
camera = scene.camera
camera_data = camera.data
scene.render.resolution_x = 1600
scene.render.resolution_y = 1600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (.62, .66, .7)

def render(name, direction, center=(0, 0, 0), scale=1.25):
    center = Vector(center)
    camera_data.ortho_scale = scale
    camera.location = center + Vector(direction) * 1.5
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(stage / (name + '.png'))
    bpy.ops.render.render(write_still=True)
    print('Rendered', name)

views = [('front', (0, -3, .12)), ('front_three_quarter', (1.7, -3, .32)),
         ('right', (3, 0, .12)), ('back_three_quarter', (1.7, 3, .32)),
         ('back', (0, 3, .12)), ('left', (-3, 0, .12))]
for name, direction in views:
    render(name, direction)
render('head_chest_detail', (0, -3, .05), (0, -.08, .3), .48)
render('harness_back_detail', (0, 3, .05), (0, -.08, .3), .48)
render('feet_front_detail', (.9, -3, .7), (0, -.15, -.435), .46)
render('repaired_foot_detail', (-1.7, -3, .45), (-.14, -.18, -.44), .25)
render('repaired_foot_back_detail', (-1.7, 3, .65), (-.14, -.18, -.44), .25)
render('hands_detail', (0, -3, .1), (-.38, -.25, -.1), .3)
render('knees_detail', (0, 3, .3), (0, -.08, -.29), .42)

for item in scene.objects:
    item.select_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.export_scene.gltf(filepath=str(stage / 'mm6_demon_cleaned.glb'), export_format='GLB',
                          use_selection=True, use_active_scene=True,
                          export_texcoords=False, export_normals=True,
                          export_materials='NONE', export_animations=False,
                          export_cameras=False, export_lights=False, export_extras=True)
report['glb_sha256'] = hashlib.sha256((stage / 'mm6_demon_cleaned.glb').read_bytes()).hexdigest()
report['glb_bytes'] = (stage / 'mm6_demon_cleaned.glb').stat().st_size
report['uv_layers'] = len(mesh.uv_layers)
report['rigged'] = False
report['textured'] = False
report['dimensions'] = list(obj.dimensions)
(stage / 'blender_cleanup_audit.json').write_text(json.dumps(report, indent=2) + '\n')
render('preview', (1.7, -3, .32))
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        space = area.spaces.active
        space.shading.type = 'SOLID'
        space.overlay.show_overlays = False
        space.region_3d.view_location = Vector((0, 0, 0))
        space.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
        space.region_3d.view_distance = 1.7
        space.region_3d.view_perspective = 'ORTHO'
bpy.ops.wm.save_as_mainfile(filepath=str(stage / 'mm6_demon_cleaned.blend'), copy=True)
print(json.dumps({key: value for key, value in report.items() if key != 'closed_surface_components'}, indent=2))
