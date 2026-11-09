"""Check the worker's unprocessed exports, using the repository's GLB and winding readers."""
import contextlib
import importlib.util
import io
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from link_static_model_lods import read_glb

spec = importlib.util.spec_from_file_location('winding', ROOT /
    'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)


def validate(path):
    doc, binary = read_glb(path)
    points = []
    triangles = 0
    vertices = 0
    for mesh in doc['meshes']:
        blend = []
        for prim in mesh['primitives']:
            mat = doc['materials'][prim['material']]
            blend.append(mat.get('alphaMode') == 'BLEND')
            pos = winding.array(doc, binary, prim['attributes']['POSITION'])
            uv = winding.array(doc, binary, prim['attributes']['TEXCOORD_0'])
            ids = winding.array(doc, binary, prim['indices']).reshape(-1, 3)
            assert np.isfinite(pos).all() and np.isfinite(uv).all(), path
            assert uv.min() >= -.001 and uv.max() <= 1.001, (path, uv.min(), uv.max())
            assert ids.max() < len(pos), path
            areas = np.linalg.norm(np.cross(pos[ids[:, 1]] - pos[ids[:, 0]],
                                            pos[ids[:, 2]] - pos[ids[:, 0]]), axis=1)
            assert areas.min() > 1e-10, (path, 'degenerate triangles', int((areas <= 1e-10).sum()))
            points.append(pos)
            triangles += len(ids)
            vertices += len(pos)
        assert len(set(blend)) == 1, (path, 'transparent material shares an opaque mesh')
    for image in doc.get('images', []):
        assert image.get('mimeType') == 'image/png' and 'bufferView' in image, (path, image)
        view = doc['bufferViews'][image['bufferView']]
        assert view['byteOffset'] + view['byteLength'] <= len(binary), path
    # Exported Blender -> glTF positions are X, Z, -Y; nodes have baked identity transforms.
    for node in doc['nodes']:
        if 'mesh' in node:
            assert 'matrix' not in node and 'translation' not in node and 'rotation' not in node, (path, node)
    pos = np.concatenate(points)
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    assert abs(lo[1]) < 1e-5, (path, 'not grounded', lo)
    assert abs(lo[0] + hi[0]) < 1e-5 and abs(lo[2] + hi[2]) < 1e-5, (path, 'not centred')
    assert hi[2] - lo[2] >= hi[0] - lo[0] - 1e-5, (path, 'long side is not horizontal Y in Blender')
    assert 4 < triangles <= 4000, (path, triangles)
    with contextlib.redirect_stdout(io.StringIO()):
        assert winding.check(path) == 0, (path, 'inverted component')
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles': triangles, 'vertices': vertices, 'bounds_gltf': [lo.tolist(), hi.tolist()],
            'materials': len(doc['materials']), 'textures': len(doc.get('images', [])),
            'winding_inverted': 0, 'uv_range_valid': True, 'grounded_centred': True,
            'triangles_degenerate': 0, 'texture_references_valid': True}


def main():
    designs = json.loads((PROJECT / 'designs.json').read_text())
    owned = {x['icon'] for x in json.loads((PROJECT / 'ownership.json').read_text())}
    assert len(designs) == len({d['icons'][0] for d in designs.values()})
    results = {}
    errors = {}
    for name, design in designs.items():
        icon = design['icons'][0]
        assert name == 'props_' + icon and set(design['icons']) <= owned
        try:
            results[icon] = validate(PROJECT / 'work' / 'exports' / f'{name}_export.glb')
        except (AssertionError, FileNotFoundError) as error:
            errors[icon] = str(error)
    report = {'valid': len(results), 'errors': errors, 'models': results}
    (PROJECT / 'review' / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print('VALID', len(results), 'ERRORS', len(errors))
    for icon, error in errors.items():
        print(icon, error)
    assert not errors


if __name__ == '__main__':
    main()
