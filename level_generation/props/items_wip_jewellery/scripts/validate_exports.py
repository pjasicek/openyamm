"""Validate this worker's exports, including glTF axes, embedded PNGs and outward winding."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from link_static_model_lods import read_glb

spec = importlib.util.spec_from_file_location(
    'winding', ROOT / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)
ownership = json.loads((PROJECT / 'ownership.json').read_text())
keep = {'7item146', '7item154', '7item264'}
expected = {row['icon'] for row in ownership} - keep
exports = {p.name.removeprefix('jewellery_').removesuffix('_export.glb'): p
           for p in (PROJECT / 'work/exports').glob('jewellery_*_export.glb')}
assert set(exports) == expected, (set(exports) - expected, expected - set(exports))
results = {}
for icon, path in sorted(exports.items()):
    document, binary = read_glb(path)
    assert 1 <= len(document['nodes']) <= 2, icon
    assert {node.get('mesh') for node in document['nodes']} == set(range(len(document['meshes']))), icon
    for node in document['nodes']:
        assert not any(k in node for k in ('matrix', 'scale', 'rotation', 'translation')), icon
        modes = {document['materials'][primitive['material']].get('alphaMode', 'OPAQUE')
                 for primitive in document['meshes'][node['mesh']]['primitives']}
        assert len(modes) == 1 and modes <= {'OPAQUE', 'BLEND'}, (icon, modes)
        assert (modes == {'BLEND'}) == node['name'].endswith('_glass'), icon
    points, count, vertex_count, uv_count = [], 0, 0, 0
    for primitive in [p for mesh in document['meshes'] for p in mesh['primitives']]:
        assert primitive.get('mode', 4) == 4, icon
        attributes = primitive['attributes']
        positions = winding.array(document, binary, attributes['POSITION'])
        normals = winding.array(document, binary, attributes['NORMAL'])
        uv = winding.array(document, binary, attributes['TEXCOORD_0'])
        indices = winding.array(document, binary, primitive['indices']).reshape(-1, 3)
        assert np.isfinite(positions).all() and np.isfinite(normals).all() and np.isfinite(uv).all(), icon
        assert np.allclose(np.linalg.norm(normals, axis=1), 1, atol=.005), icon
        assert uv.min() >= -.0001 and uv.max() <= 1.0001, (icon, uv.min(), uv.max())
        assert indices.min() >= 0 and indices.max() < len(positions), icon
        a, b, c = (positions[indices[:, i]] for i in range(3))
        assert (np.linalg.norm(np.cross(b - a, c - a), axis=1) > 1e-10).all(), icon
        mat = document['materials'][primitive['material']]
        if 'normalTexture' in mat:
            ua, ub, uc = (uv[indices[:, i]] for i in range(3))
            edge1, edge2 = ub - ua, uc - ua
            assert (np.abs(edge1[:, 0] * edge2[:, 1] - edge1[:, 1] * edge2[:, 0]) > 1e-10).all(), icon
        if mat.get('alphaMode') == 'BLEND':
            assert mat['name'].endswith('_glass'), icon
            assert mat['pbrMetallicRoughness']['metallicFactor'] == 0, icon
            keys = [tuple(np.round(position, 5)) for position in positions]
            for part in winding.components(indices, keys):
                triangle = indices[part]
                pa, pb, pc = (positions[triangle[:, i]] for i in range(3))
                volume = np.einsum('ij,ij->i', pa, np.cross(pb, pc)).sum() / 6
                assert volume > 0, (icon, 'inverted glass shell')
        points.append(positions)
        count += len(indices)
        vertex_count += len(positions)
        uv_count += len(uv)
    points = np.concatenate(points)
    lower, upper = points.min(axis=0), points.max(axis=0)
    # glTF Y is vertical; horizontal longest side is Z after Blender +Y -> glTF -Z.
    assert abs(lower[1]) < 1e-5, (icon, lower)
    assert abs(lower[0] + upper[0]) < 1e-5 and abs(lower[2] + upper[2]) < 1e-5, icon
    assert upper[2] - lower[2] >= upper[0] - lower[0] - 1e-5, icon
    assert count <= 3200 and count > 0 and uv_count == vertex_count, icon
    for image in document.get('images', []):
        assert 'uri' not in image and image.get('mimeType') == 'image/png', (icon, image)
        view = document['bufferViews'][image['bufferView']]
        offset = view.get('byteOffset', 0)
        png = Image.open(io.BytesIO(binary[offset:offset + view['byteLength']]))
        assert all(size > 0 and size & (size - 1) == 0 for size in png.size), (icon, png.size)
        png.verify()
    for mat in document['materials']:
        assert not mat.get('doubleSided', False) and mat.get('alphaMode', 'OPAQUE') in ('OPAQUE', 'BLEND'), icon
        pbr = mat.get('pbrMetallicRoughness', {})
        if 'baseColorTexture' not in pbr:
            factors = np.array(pbr.get('baseColorFactor', [1, 1, 1, 1])[:3])
            srgb = np.where(factors <= .0031308, factors * 12.92, 1.055 * factors ** (1 / 2.4) - .055) * 255
            assert srgb.min() >= 29.99 and srgb.max() <= 243.01, (icon, mat['name'], srgb)
    with contextlib.redirect_stdout(io.StringIO()):
        assert winding.check(path) == 0, icon
    results[icon] = {'triangles': count, 'vertices': vertex_count, 'materials': len(document['materials']),
                     'images': len(document.get('images', [])), 'meshes': len(document['meshes']),
                     'bounds_gltf': [lower.tolist(), upper.tolist()],
                     'uvs_in_0_1': True, 'outward_winding': True, 'grounded': True}
(PROJECT / 'work/validation.json').write_text(json.dumps(results, indent=2) + '\n')
print(f'{len(results)} assigned exports passed geometry, UV, PNG, grounding and winding checks; {len(keep)} retained')
