"""Validate owned unprocessed GLB exports before installing them; retain per-design measurements."""
import io
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
sys.path.insert(0, str(repo / 'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import array, check
from link_static_model_lods import read_glb

designs = json.loads((project / 'designs.json').read_text())
for name in sys.argv[1:]:
    assert name in designs, name
    path = project / 'work/codex_tex' / f'{name}_export.glb'
    document, binary = read_glb(path)
    triangles, all_positions = 0, []
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            attributes = primitive['attributes']
            positions = array(document, binary, attributes['POSITION'])
            normals = array(document, binary, attributes['NORMAL'])
            uv = array(document, binary, attributes['TEXCOORD_0'])
            indices = array(document, binary, primitive['indices']).reshape(-1, 3)
            assert all(np.isfinite(values).all() for values in [positions, normals, uv])
            assert uv.min() >= -1e-5 and uv.max() <= 1.00001
            assert indices.max() < len(positions)
            areas = np.linalg.norm(np.cross(positions[indices[:, 1]] - positions[indices[:, 0]],
                                            positions[indices[:, 2]] - positions[indices[:, 0]]), axis=1)
            assert (areas > 1e-12).all(), (name, 'degenerate triangles')
            assert (np.abs(np.linalg.norm(normals, axis=1) - 1) < 0.001).all()
            triangles += len(indices)
            all_positions.append(positions)
    positions = np.concatenate(all_positions)
    low, high = positions.min(axis=0), positions.max(axis=0)
    assert abs(low[1]) < 0.0001, (name, 'lowest point is not zero', low)
    assert max(abs(low[[0, 2]] + high[[0, 2]])) < 0.0001, (name, 'footprint not centred')
    assert 0 < triangles <= 3500, (name, triangles)
    assert len(document['images']) == 3
    if designs[name].get('lining'):
        lining = designs[name]['lining']
        materials = [material for material in document['materials']
                     if material['name'].startswith('physical_')]
        assert len(materials) == 1, (name, 'missing separate lining')
        pbr = materials[0]['pbrMetallicRoughness']
        assert pbr['metallicFactor'] == 0
        expected_roughness = 0.6 if lining['kind'] == 'leather' else 0.85
        assert abs(pbr['roughnessFactor'] - expected_roughness) < 1e-5
        assert len({primitive['material'] for mesh in document['meshes']
                    for primitive in mesh['primitives']}) == 2
    for image in document['images']:
        assert image['mimeType'] == 'image/png' and 'bufferView' in image
        view = document['bufferViews'][image['bufferView']]
        offset = view.get('byteOffset', 0)
        picture = Image.open(io.BytesIO(binary[offset:offset + view['byteLength']]))
        assert picture.size == (512, 512), (name, picture.size)
    assert check(path) == 0, name
    report = {'design': name, 'export_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'triangles': triangles, 'finite_attributes': True, 'uv_range_valid': True,
              'degenerate_triangles': 0, 'embedded_png_maps': 3, 'texture_size': 512,
              'bounds_gltf': [low.tolist(), high.tolist()], 'inverted_closed_parts': 0}
    (project / 'review' / f'{name}_export_check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(name, triangles, 'triangles: export checks passed')
