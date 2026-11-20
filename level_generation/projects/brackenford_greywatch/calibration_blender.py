"""Run through Blender MCP: author and export a two-room native-compiler calibration.

This is a fixture, not either finished map. Its output tests Blender's axis, UV and
node-name export through the existing glTF importer and native BLV writer.
"""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path('/home/pjasicek/github/OpenYAMM')
OUTPUT = ROOT / 'level_generation/projects/brackenford_greywatch/calibration'
OUTPUT.mkdir(parents=True, exist_ok=True)
SCALE = 128
scene = bpy.data.scenes.new('Greywatch compiler calibration')
bpy.context.window.scene = scene
texture_paths = {p.stem.lower(): p for p in (ROOT / 'assets_dev/worlds/mm8/textures').iterdir()
                 if p.suffix.lower() == '.bmp'}
metadata = {
    'format_version': 2, 'kind': 'indoor_geometry', 'map_file': 'calibration.blv',
    'source': {'authoring_file': 'calibration.blend', 'asset_path': 'calibration.glb',
               'coordinate_system': 'blender_z_up', 'unit_scale': SCALE,
               'import': {'source_format': 'glb', 'reserve_sector_zero': True,
                          'merge_coplanar_faces': True, 'generate_bsp': True,
                          'generate_outlines': True}},
    'materials': [], 'portals': [{'id': 'entry_gallery', 'source_node': 'PORTAL_entry_gallery',
                                'front_room': 'room_entry', 'back_room': 'room_gallery'}],
    'rooms': [{'id': 'room_entry', 'source_nodes': ['ROOM_entry']},
              {'id': 'room_gallery', 'source_nodes': ['ROOM_gallery']}],
    'surfaces': [], 'mechanisms': [], 'entities': [], 'lights': [], 'spawns': [],
}
materials = {}
for key in ['GSton1WL', 'GSton1FL', 'TFB11', 'gt002b']:
    image = bpy.data.images.load(str(texture_paths[key.lower()]), check_existing=True)
    image.pack()
    material = bpy.data.materials.new(key)
    material.use_nodes = True
    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Roughness'].default_value = 1
    material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    materials[key] = material
    metadata['materials'].append({'id': key, 'source_material': material.name, 'texture': key,
                                  'texture_width': image.size[0], 'texture_height': image.size[1]})


def make_mesh(name, panels):
    vertices, faces, uv_values, material_keys = [], [], [], []
    for points, key, inward in panels:
        points = [Vector(p) for p in points]
        normal = (points[1] - points[0]).cross(points[2] - points[0])
        if normal.dot(Vector(inward)) < 0:
            points.reverse()
        offset = len(vertices)
        vertices.extend(tuple(p / SCALE) for p in points)
        faces.append(tuple(range(offset, offset + len(points))))
        # Project onto the two dominant tangent axes. One texel per four game units.
        n = normal.normalized()
        axis = max(range(3), key=lambda i: abs(n[i]))
        tangent = [i for i in range(3) if i != axis]
        info = next(v for v in metadata['materials'] if v['id'] == key)
        uv_values.extend((p[tangent[0]] / (4 * info['texture_width']),
                          p[tangent[1]] / (4 * info['texture_height'])) for p in points)
        material_keys.append(key)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    for mat in materials.values():
        mesh.materials.append(mat)
    for polygon, key in zip(mesh.polygons, material_keys):
        polygon.material_index = list(materials).index(key)
    layer = mesh.uv_layers.new()
    for loop, uv in zip(layer.data, uv_values):
        loop.uv = uv
    return obj


for name, left, right in [('ROOM_entry', 0, 1024), ('ROOM_gallery', 1024, 2048)]:
    panels = [
        ([(left,0,0),(right,0,0),(right,1024,0),(left,1024,0)], 'GSton1FL', (0,0,1)),
        ([(left,0,768),(right,0,768),(right,1024,768),(left,1024,768)], 'TFB11', (0,0,-1)),
        ([(left,0,0),(right,0,0),(right,0,768),(left,0,768)], 'GSton1WL', (0,1,0)),
        ([(left,1024,0),(right,1024,0),(right,1024,768),(left,1024,768)], 'GSton1WL', (0,-1,0)),
    ]
    for x, inward in [(left, (1,0,0)), (right, (-1,0,0))]:
        spans = [(0,1024,0,768)] if x != 1024 else [(0,384,0,768),(640,1024,0,768),(384,640,384,768)]
        for ya, yb, za, zb in spans:
            panels.append(([(x,ya,za),(x,yb,za),(x,yb,zb),(x,ya,zb)], 'GSton1WL', inward))
    make_mesh(name, panels)

make_mesh('PORTAL_entry_gallery', [([(1024,384,0),(1024,640,0),(1024,640,384),(1024,384,384)],
                                   'GSton1WL', (-1,0,0))])
make_mesh('TRIGGER_uv_panel', [([(128,1,128),(384,1,128),(384,1,384),(128,1,384)], 'gt002b', (0,1,0))])
metadata['surfaces'].append({'id': 'uv_panel', 'source_node': 'TRIGGER_uv_panel',
                             'trigger': {'event_id': 101, 'type': 'click'}})

# Keep the authoring scene in Z-up and tell the glTF exporter not to change axes.
bpy.ops.export_scene.gltf(filepath=str(OUTPUT / 'calibration.glb'), export_format='GLB',
                         use_active_scene=True, export_yup=False, export_cameras=False,
                         export_lights=False, export_apply=True)
(OUTPUT / 'calibration.geometry.yml').write_text(json.dumps(metadata, indent=2) + '\n')
(OUTPUT / 'expectations.json').write_text(json.dumps({
    'bounds_game': [[0,0,0],[2048,1024,768]], 'occupied_sectors': 2,
    'portal_sector_pair': [1,2], 'surface_event': 101,
    'texture_dimensions': {v['texture']: [v['texture_width'],v['texture_height']] for v in metadata['materials']},
    'scope': 'Compiler calibration only; derived BSP/automap verified, no scene gameplay state',
}, indent=2) + '\n')
bpy.data.libraries.write(str(OUTPUT / 'calibration.blend'), {scene}, fake_user=True)
print(json.dumps({'output': str(OUTPUT), 'objects': len(scene.objects), 'materials': metadata['materials']}))
