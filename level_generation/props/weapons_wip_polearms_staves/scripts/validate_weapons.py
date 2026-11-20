"""Check exported polearms and staves, including culling, closed surfaces, UVs, textures and grounding.

Does not install or change shared content.
"""
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location(
    'winding', ROOT / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)


def geometry_hash(path):
    doc, binary = winding.read_glb(path)
    digest = hashlib.sha256()
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            for attribute in ('POSITION', 'NORMAL', 'TEXCOORD_0'):
                digest.update(winding.array(doc, binary, primitive['attributes'][attribute]).tobytes())
            digest.update(winding.array(doc, binary, primitive['indices']).tobytes())
    return digest.hexdigest()


def check(path, design):
    doc, binary = winding.read_glb(path)
    assert all(not m.get('doubleSided', False) for m in doc['materials']), path
    assert all(not any(k in n for k in ('translation', 'rotation', 'scale', 'matrix')) for n in doc['nodes']), path
    all_positions, triangles, vertices, parts = [], 0, 0, 0
    lod_indices = {i for m in doc['meshes'] for i in m.get('extras', {}).get('openyamm_lods', [])}
    lod_triangles = []
    for mesh_index, mesh in enumerate(doc['meshes']):
        if mesh_index in lod_indices:
            lod_triangles.append(sum(doc['accessors'][p['indices']]['count'] // 3 for p in mesh['primitives']))
        for prim in mesh['primitives']:
            pos = winding.array(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
            uv = winding.array(doc, binary, prim['attributes']['TEXCOORD_0'])
            normal = winding.array(doc, binary, prim['attributes']['NORMAL'])
            tris = winding.array(doc, binary, prim['indices']).reshape(-1, 3)
            assert np.isfinite(pos).all() and np.isfinite(uv).all()
            assert uv.min() >= -1e-6 and uv.max() <= 1.000001
            assert np.allclose(np.linalg.norm(normal, axis=1), 1, atol=1e-4)
            area = np.linalg.norm(np.cross(pos[tris[:, 1]] - pos[tris[:, 0]],
                                           pos[tris[:, 2]] - pos[tris[:, 0]]), axis=1) / 2
            assert area.min() > 1e-10, (path, area.min())
            keys = [tuple(np.round(p, 6)) for p in pos]
            for part in winding.components(tris, keys):
                selected = tris[part]
                edges = Counter(tuple(sorted((keys[t[i]], keys[t[(i + 1) % 3]])))
                                for t in selected for i in range(3))
                assert all(n == 2 for n in edges.values()), (path, mesh['name'], 'open/non-manifold surface')
                a, b, c = (pos[selected[:, i]] for i in range(3))
                volume = np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6
                assert volume > 0, (path, mesh['name'], volume)
                parts += 1
            if mesh_index not in lod_indices:
                triangles += len(tris)
                vertices += len(pos)
                all_positions.append(pos)
    pos = np.concatenate(all_positions)
    low, high = pos.min(axis=0), pos.max(axis=0)
    assert abs(low[1]) < 1e-5, (path, low)
    assert np.allclose((low + high)[[0, 2]], 0, atol=1e-5), (path, low, high)
    assert triangles <= min(15000, design['tris']), (path, triangles)
    for image in doc.get('images', []):
        assert image.get('mimeType') == 'image/png' and 'bufferView' in image, (path, image)
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        assert binary[start:start + 8] == b'\x89PNG\r\n\x1a\n'
    assert winding.check(path) == 0
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles': triangles, 'lod_triangles': lod_triangles, 'vertices': vertices, 'closed_parts': parts,
            'materials': len(doc['materials']), 'embedded_pngs': len(doc.get('images', [])),
            'gltf_bounds': [low.tolist(), high.tolist()], 'checks': 'passed'}


def main():
    designs = json.loads((HERE / 'designs.json').read_text())
    owned = json.loads((HERE / 'ownership.json').read_text())
    assert {e['master_icon'] for e in designs.values()} == {e['icon'] for e in owned}
    reports = []
    failures = []
    for path in sorted((HERE / 'work/finished').glob('*_export.glb')):
        name = path.name.removesuffix('_export.glb')
        assert name in designs
        try:
            reports.append({'icon': designs[name]['master_icon'], **check(path, designs[name])})
        except AssertionError as error:
            failures.append({'icon': designs[name]['master_icon'], 'error': str(error)})
    (HERE / 'review/validation.json').write_text(json.dumps(reports, indent=2) + '\n')
    (HERE / 'review/validation_failures.json').write_text(json.dumps(failures, indent=2) + '\n')
    print(len(reports), 'exports passed')
    assert not failures, failures
    assert geometry_hash(HERE / 'work/finished/pole_6staff4_export.glb') == geometry_hash(
        HERE / 'work/finished/pole_staff3_export.glb'), 'Merlin and Power Staff must share geometry, including LODs'


if __name__ == '__main__':
    main()
