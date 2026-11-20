"""Export the current Brackenford BModels with packed textures using Blender's glTF exporter.

Run: blender --background --factory-startup --python path/to/export_shareable_bmodels.py
"""

import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

import bpy
from mathutils import Vector


PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
OUTPUT = PROJECT / 'dist/brackenford_buildings_glb'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    assert (magic, version, length) == (b'glTF', 2, len(data)), path
    size, kind = struct.unpack_from('<I4s', data, 12)
    assert kind == b'JSON', path
    document = json.loads(data[20:20 + size])
    assert all('uri' not in item for item in document.get('buffers', [])), path
    assert document.get('images'), path
    for image in document['images']:
        assert 'uri' not in image and 'bufferView' in image, (path, image)
        assert image['mimeType'] == 'image/png', (path, image)
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            assert {'POSITION', 'NORMAL', 'TEXCOORD_0'} <= primitive['attributes'].keys(), path
            assert 'material' in primitive, path
    return document


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = PROJECT / 'source/lg01.blend'
    native_path = PROJECT / 'runtime/worlds/mm8/maps/lg01.odm'
    semantics = json.loads((PROJECT / 'source/lg01.semantic.json').read_text())
    native = parse_odm_file(native_path)['payload']['bmodels']
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scale = scene['native_units_per_blender_unit']
    objects = {obj['semantic_id']: obj for obj in scene.objects if obj.name.startswith('BMODEL_')}
    assert len(objects) == len(native) == len(semantics['bmodels'])
    inventory = []
    for entry, model in zip(semantics['bmodels'], native):
        obj = objects[entry['id']]
        assert model['index'] == entry['index']
        assert len(obj.data.polygons) == len(model['faces']) == entry['faces']
        textures = set()
        for polygon, face in zip(obj.data.polygons, model['faces']):
            actual = [tuple(round(value * scale) for value in obj.matrix_world @ obj.data.vertices[i].co)
                      for i in polygon.vertices]
            expected = [tuple(model['vertices'][i][axis] for axis in 'xyz') for i in face['vertex_indices']]
            assert actual == expected, (entry['id'], polygon.index, 'native geometry mismatch')
            material = obj.data.materials[polygon.material_index]
            texture = material.name.removeprefix('BF_').lower()
            assert texture == face['texture_name'].lower(), (entry['id'], texture, face['texture_name'])
            images = [node.image for node in material.node_tree.nodes if node.type == 'TEX_IMAGE']
            assert len(images) == 1 and images[0].packed_file, (entry['id'], texture)
            assert min(images[0].size) > 0, texture
            textures.add(texture)
        obj.data.calc_loop_triangles()
        obj['runtime_bmodel_index'] = entry['index']
        inventory.append({**entry, 'triangles': len(obj.data.loop_triangles), 'textures': sorted(textures),
                          'geometry_origin': obj.get('reuse_source', 'Brackenford generated geometry')})

    groups = [(f"buildings/{entry['id']}", [entry['id'], entry['id'] + '_door'])
              for entry in semantics['buildings']]
    for prefix in ('castle', 'bridge', 'cave'):
        groups.append((f'structures/{prefix}', [name for name in objects if name.startswith(prefix + '_')]))
    groups.extend((f"props/{entry['id']}", [entry['id']]) for entry in semantics['content_landmarks'])
    flattened = [name for _, names in groups for name in names]
    assert len(flattened) == len(set(flattened)) == len(objects)
    assert set(flattened) == set(objects)

    # A small export-only scene avoids traversing vegetation and authoring previews for each file.
    export_scene = bpy.data.scenes.new('Brackenford BModels export')
    for obj in objects.values():
        export_scene.collection.objects.link(obj)
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False
    bpy.context.window.scene = export_scene
    files = []
    exports = []
    for relative, names in [('brackenford_all_bmodels_in_place', list(objects))] + groups:
        selected = [objects[name] for name in names]
        bpy.ops.object.select_all(action='DESELECT')
        points = [obj.matrix_world @ vertex.co for obj in selected for vertex in obj.data.vertices]
        minimum = Vector([min(point[axis] for point in points) for axis in range(3)])
        maximum = Vector([max(point[axis] for point in points) for axis in range(3)])
        origin = Vector((0, 0, 0)) if relative.startswith('brackenford_all') else Vector(
            ((minimum.x + maximum.x) / 2, (minimum.y + maximum.y) / 2, minimum.z))
        for obj in selected:
            obj.select_set(True)
            # Bake centering into mesh vertices, so individual assets also have useful object origins.
            for vertex in obj.data.vertices:
                vertex.co -= origin
        path = OUTPUT / (relative + '.glb')
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = bpy.ops.export_scene.gltf(
                filepath=str(path), export_format='GLB', use_selection=True,
                export_image_format='AUTO', export_texcoords=True, export_normals=True,
                export_materials='EXPORT', export_yup=True, export_animations=False,
                export_cameras=False, export_lights=False, export_extras=True)
            assert result == {'FINISHED'}, path
        finally:
            for obj in selected:
                for vertex in obj.data.vertices:
                    vertex.co += origin
        document = read_glb(path)
        mesh_nodes = [node for node in document['nodes'] if 'mesh' in node]
        assert len(mesh_nodes) == len(names), (path, len(mesh_nodes), len(names))
        triangles = sum(document['accessors'][primitive['indices']]['count'] // 3
                        for mesh in document['meshes'] for primitive in mesh['primitives'])
        expected_triangles = sum(len(obj.data.loop_triangles) for obj in selected)
        assert triangles == expected_triangles, (path, triangles, expected_triangles)
        exports.append({'file': str(path.relative_to(OUTPUT)), 'bmodels': names,
                        'original_origin_native_xyz': [value * scale for value in origin],
                        'triangles': triangles, 'embedded_textures': len(document['images']),
                        'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        files.append(path)
        print('EXPORTED', relative, len(names), 'BModels', flush=True)

    # Reimport every delivery to check that an independent importer can reconstruct meshes and textures.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for entry in exports:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(OUTPUT / entry['file']))
        imported = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        assert len(imported) == len(entry['bmodels']), entry['file']
        assert sum(len(obj.data.polygons) for obj in imported) == entry['triangles'], entry['file']
        used_images = {node.image for obj in imported for material in obj.data.materials
                       for node in material.node_tree.nodes if node.type == 'TEX_IMAGE'}
        assert len(used_images) == entry['embedded_textures'], entry['file']
        assert all(min(image.size) > 0 for image in used_images), entry['file']

    report = {'map': 'lg01.odm / Brackenford', 'bmodel_count': len(inventory),
              'source_faces': sum(item['faces'] for item in inventory), 'glb_count': len(exports),
              'native_units_per_gltf_unit': scale, 'gltf_axes': 'X, Z, -Y from native X, Y, Z',
              'source_blend_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'source_odm_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest(),
              'checks': ['All BModels covered exactly once by individual assets',
                         'Every source polygon matches native ODM vertices, winding, and material',
                         'Every GLB embeds PNG textures, preserves UVs and normals, and has no external buffers',
                         'Exported triangle and mesh counts match source',
                         'Every GLB reimported successfully with expected meshes, triangles, and textures'],
              'bmodels': inventory, 'exports': exports}
    manifest = OUTPUT / 'manifest.json'
    manifest.write_text(json.dumps(report, indent=2) + '\n')
    readme = OUTPUT / 'README.txt'
    readme.write_text(
        'BRACKENFORD BUILDINGS AND BMODELS\n\n'
        '41 self-contained GLB (glTF 2.0) files; all textures embedded as PNG.\n'
        'Open in Blender or another glTF-compatible viewer without OpenYAMM installed.\n\n'
        'buildings/: 29 buildings, each including its separate door mesh.\n'
        'structures/: assembled castle (12 BModels), bridge (5), and cave entrance (4).\n'
        'props/: 8 placed props: 4 chests, 2 wells, fountain, and obelisk.\n'
        'brackenford_all_bmodels_in_place.glb: all 87 BModels at original relative map positions.\n'
        'Each BModel remains a named, separate mesh, with its runtime index in custom properties.\n'
        'Individual assets are centered horizontally and grounded at their lowest vertex.\n'
        'Map orientation is preserved. Scale: one glTF unit = 128 native game units.\n'
        'glTF uses Y up: native (X,Y,Z) becomes (X,Z,-Y), divided by 128.\n'
        'manifest.json records original placement offsets, materials, counts, checks, and hashes.\n\n'
        'Scope: exterior BModel geometry and materials only. Terrain, vegetation, actors,\n'
        'interiors, game logic, animated water, and runtime lighting are not included.\n'
        'Materials retain the authored texture UVs, nearest filtering, and rough surfaces.\n\n'
        'Provenance: building/structure geometry was generated for Brackenford, calibrated\n'
        'against MM8 Ravenshore architecture. Textures are existing MM8 artwork. The chests,\n'
        'wells, fountain, and obelisk reuse MM8 out02.odm geometry; exact source BModel indices\n'
        'are recorded in the manifest. This archive does not grant a new license to MM8 assets.\n')
    files.extend([manifest, readme])
    archive = PROJECT / 'dist/brackenford_buildings_glb.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in sorted(files):
            output.write(path, str(Path(OUTPUT.name) / path.relative_to(OUTPUT)))
    with zipfile.ZipFile(archive) as output:
        assert output.testzip() is None
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size,
                      'glb_files': len(exports), 'bmodels': len(inventory), 'validation': 'passed'}))


if __name__ == '__main__':
    main()
