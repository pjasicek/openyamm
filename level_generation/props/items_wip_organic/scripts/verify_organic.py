"""Validate the owned exports and save reproducible geometry/texture receipts."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[2]
sys.path.insert(0, str(REPO / 'level_generation/decorations/mm8_3d/animated/scripts'))
import check_winding as winding


def verify(path):
    document, binary = winding.read_glb(path)
    positions, triangle_count, degenerate, boundary = [], 0, 0, 0
    min_uv, max_uv = 1, 0
    for mesh in document['meshes']:
        edges = Counter()
        for primitive in mesh['primitives']:
            attributes = primitive['attributes']
            points = winding.array(document, binary, attributes['POSITION'])
            assert np.isfinite(points).all(), path
            positions.append(points)
            uv = winding.array(document, binary, attributes['TEXCOORD_0'])
            assert np.isfinite(uv).all(), path
            min_uv, max_uv = min(min_uv, float(uv.min())), max(max_uv, float(uv.max()))
            triangles = winding.array(document, binary, primitive['indices']).reshape(-1, 3)
            triangle_count += len(triangles)
            a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
            areas = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
            degenerate += int(np.sum(areas < 1e-10))
            keys = [tuple(np.round(p, 6)) for p in points]
            for tri in triangles:
                for n in range(3):
                    edges[tuple(sorted((keys[tri[n]], keys[tri[(n + 1) % 3]])))] += 1
        boundary += sum(n == 1 for n in edges.values())
    assert degenerate == 0, (path.name, 'degenerate triangles', degenerate)
    assert -1e-6 <= min_uv <= max_uv <= 1.000001, (path.name, min_uv, max_uv)
    assert triangle_count < 4000, path
    points = np.concatenate(positions)
    low, high = points.min(axis=0), points.max(axis=0)
    # glTF is Y-up; the horizontal footprint is X/Z.
    assert abs(low[1]) < 1e-5, (path.name, low)
    assert max(abs((low + high)[[0, 2]])) < 1e-5, (path.name, low, high)
    assert abs(max((high - low)[[0, 2]]) - 1) < 1e-5, path
    for image in document.get('images', []):
        assert 'bufferView' in image, (path.name, 'unembedded image', image)
        assert image['mimeType'] == 'image/png', (path.name, image)
    assert winding.check(path) == 0, path
    if path.name == 'item303_export.glb':
        glass = [n for n, mat in enumerate(document['materials']) if mat.get('alphaMode') == 'BLEND']
        assert len(glass) == 1
        assert len(document['meshes']) == 2, 'Glass must have its own mesh node'
    if path.name == 'item161_export.glb':
        assert all('COLOR_0' in p['attributes'] for m in document['meshes'] for p in m['primitives'])
    return {'export': str(path.relative_to(PROJECT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles': triangle_count, 'degenerate_triangles': degenerate, 'boundary_edges': boundary,
            'uv_range': [min_uv, max_uv], 'gltf_bounds': [low.tolist(), high.tolist()],
            'embedded_pngs': len(document.get('images', [])), 'winding_passed': True}


def main():
    owned = {i['icon'] for i in json.loads((PROJECT / 'ownership.json').read_text())}
    files = sorted((PROJECT / 'work/blender').glob('*_export.glb'))
    assert len(files) == 14
    files += sorted(p for p in (PROJECT / 'work/codex_tex').glob('organic_*_export.glb')
                    if not p.name.endswith('_clay_export.glb'))
    receipts = []
    for path in files:
        assert path.name.removesuffix('_export.glb').removeprefix('organic_') in owned
        receipts.append(verify(path))
    (PROJECT / 'review/validation.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(f'PASS: {len(receipts)} owned exports, {sum(r["triangles"] for r in receipts)} triangles')


if __name__ == '__main__':
    main()
