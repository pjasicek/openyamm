"""Check exported sculptures, including culling, closed surfaces, UVs, textures and grounding.

Also writes icon/above/three-quarter/low comparison sheets. Does not install or change shared content.
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


def check(path, design):
    doc, binary = winding.read_glb(path)
    assert all(not m.get('doubleSided', False) for m in doc['materials']), path
    assert all(not any(k in n for k in ('translation', 'rotation', 'scale', 'matrix')) for n in doc['nodes']), path
    all_positions, triangles, vertices, parts = [], 0, 0, 0
    for mesh in doc['meshes']:
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
            triangles += len(tris)
            vertices += len(pos)
            all_positions.append(pos)
    pos = np.concatenate(all_positions)
    low, high = pos.min(axis=0), pos.max(axis=0)
    assert abs(low[1]) < 1e-5, (path, low)
    assert np.allclose((low + high)[[0, 2]], 0, atol=1e-5), (path, low, high)
    assert triangles <= design['tris'], (path, triangles)
    for image in doc.get('images', []):
        assert image.get('mimeType') == 'image/png' and 'bufferView' in image, (path, image)
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        assert binary[start:start + 8] == b'\x89PNG\r\n\x1a\n'
    assert winding.check(path) == 0
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'triangles': triangles, 'vertices': vertices, 'closed_parts': parts,
            'materials': len(doc['materials']), 'embedded_pngs': len(doc.get('images', [])),
            'gltf_bounds': [low.tolist(), high.tolist()], 'checks': 'passed'}


def sheets(designs, group, views):
    icons = [e['master_icon'] for e in designs.values() if e['route'] == group]
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    for start in range(0, len(icons), 6):
        canvas = Image.new('RGB', (1280, 1100), (28, 31, 38))
        draw = ImageDraw.Draw(canvas)
        for n, icon in enumerate(icons[start:start + 6]):
            x, y = n % 2 * 640, n // 2 * 360
            entry = designs['sculpture_' + icon]
            draw.text((x + 5, y + 5), icon + ' | ' + entry['title'], fill='white', font=font)
            paths = [ROOT / 'assets_dev/engine/icons_x2' / (icon + '.png')]
            if views:
                folder = 'blender' if group == 'blender' else 'codex_tex'
                paths += [HERE / 'review' / folder / (icon + '_' + v + '.png') for v in views]
            else:
                paths += [HERE / 'meshy' / ('sculpture_' + icon) / 'references_hd/00_three_quarter.png']
            width = 640 // len(paths)
            for j, path in enumerate(paths):
                if not path.exists():
                    draw.text((x + j * width + 5, y + 120), 'DEFERRED', fill='orange', font=font)
                    continue
                image = Image.open(path).convert('RGBA')
                image.thumbnail((width - 8, 300))
                canvas.paste(image, (x + j * width + (width - image.width) // 2,
                                    y + 35 + (300 - image.height) // 2), image)
        canvas.save(HERE / 'review' / f'{group}_comparison_{start // 6 + 1}.png')


def main():
    designs = json.loads((HERE / 'designs.json').read_text())
    ownership = json.loads((HERE / 'ownership.json').read_text())
    assert {e['master_icon'] for e in designs.values()} == {e['icon'] for e in ownership}
    reports = []
    for family, route in [('blender', 'blender'), ('codex_tex', 'meshy')]:
        for path in sorted((HERE / 'work' / family).glob('*_export.glb')):
            name = path.name.removesuffix('_export.glb')
            assert name in designs and designs[name]['route'] == route
            reports.append({'icon': designs[name]['master_icon'], **check(path, designs[name])})
    (HERE / 'review/validation.json').write_text(json.dumps(reports, indent=2) + '\n')
    sheets(designs, 'blender', ['above', 'three_quarter', 'low'])
    sheets(designs, 'meshy', ['above', 'three_quarter', 'low'])
    print(len(reports), 'exports passed')


if __name__ == '__main__':
    main()
