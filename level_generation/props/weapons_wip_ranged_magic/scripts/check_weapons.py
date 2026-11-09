"""Validate owned exports after GLB reimport, before any installation."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from link_static_model_lods import read_glb

spec = importlib.util.spec_from_file_location('winding', ROOT /
    'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(icon):
    path = HERE / f'work/exports/item_{icon}.glb'
    document, binary = read_glb(path)
    assert not document.get('extensionsRequired')
    assert len(document['materials']) == 1
    material = document['materials'][0]
    assert not material.get('doubleSided')
    assert material.get('alphaMode', 'OPAQUE') == 'OPAQUE'
    pbr = material['pbrMetallicRoughness']
    assert 'metallicRoughnessTexture' in pbr and 'baseColorTexture' in pbr and 'normalTexture' in material
    assert winding.check(path) == 0
    counts = []
    points = []
    for mesh_index, mesh in enumerate(document['meshes']):
        count = 0
        for prim in mesh['primitives']:
            pos = winding.array(document, binary, prim['attributes']['POSITION']).astype(float)
            uv = winding.array(document, binary, prim['attributes']['TEXCOORD_0'])
            normals = winding.array(document, binary, prim['attributes']['NORMAL'])
            tris = winding.array(document, binary, prim['indices']).astype(int).reshape(-1, 3)
            assert np.isfinite(pos).all() and np.isfinite(uv).all() and np.isfinite(normals).all()
            assert uv.min() >= 0 and uv.max() <= 1
            assert np.allclose(np.linalg.norm(normals, axis=1), 1, atol=.002)
            a, b, c = [pos[tris[:, j]] for j in range(3)]
            areas = np.linalg.norm(np.cross(b - a, c - a), axis=1) / 2
            assert areas.min() > 1e-12, (icon, 'degenerate', areas.min())
            if mesh_index == 0:
                points.append(pos)
            count += len(tris)
        counts.append(count)
    base_index = document['nodes'][document['scenes'][0]['nodes'][0]]['mesh']
    base_mesh = document['meshes'][base_index]
    chain = [base_index] + base_mesh.get('extras', {}).get('openyamm_lods', [])
    lod_counts = [counts[i] for i in chain]
    assert lod_counts[0] < 15000
    assert all(.35 < b / a < .65 for a, b in zip(lod_counts, lod_counts[1:]))
    # Vertex data is authored directly in the grounded glTF coordinate system.
    prim = base_mesh['primitives'][0]
    pos = winding.array(document, binary, prim['attributes']['POSITION'])
    low, high = pos.min(axis=0), pos.max(axis=0)
    assert abs(low[1]) < 1e-6, (icon, 'ground', low)
    assert abs(high[0] + low[0]) < 1e-5 and abs(high[2] + low[2]) < 1e-5
    assert abs(max(high[0] - low[0], high[2] - low[2]) - 1) < 1e-5
    assert high[2] - low[2] >= high[0] - low[0] - 1e-5
    for kind in ['clay', 'textured']:
        for view in ['top', 'threequarter', 'low', 'underside']:
            assert (HERE / f'review/{kind}/{icon}_{view}.png').exists()
    sizes = {}
    for im in document['images']:
        view = document['bufferViews'][im['bufferView']]
        start = view.get('byteOffset', 0)
        image = Image.open(io.BytesIO(binary[start:start + view['byteLength']]))
        assert image.format == 'PNG' and image.size == (2048, 2048)
        sizes[im['name']] = list(image.size)
        if 'mr' in im['name']:
            assert set(np.unique(np.asarray(image)[:, :, 2])) == {0, 255}
    assert len(sizes) == 3
    # UV wireframe is an inspectable record of deliberate material swatch reuse.
    sheet = Image.open(HERE / 'textures/weapon_base.png').resize((1024, 1024))
    draw = ImageDraw.Draw(sheet)
    uv = winding.array(document, binary, prim['attributes']['TEXCOORD_0'])
    tris = winding.array(document, binary, prim['indices']).astype(int).reshape(-1, 3)
    for tri in tris:
        line = [(int(uv[i, 0] * 1023), int((1 - uv[i, 1]) * 1023)) for i in tri]
        draw.line(line + line[:1], fill=(70, 180, 220))
    sheet.save(HERE / f'review/uv/{icon}.png')
    return {'sha256': sha(path), 'lod_triangles': lod_counts, 'texture_sizes': sizes,
            'bounds_gltf': [low.tolist(), high.tolist()], 'material_count': 1,
            'checks': ['winding', 'finite normals/UVs', 'UV bounds', 'triangle area', 'ground/footprint',
                       'embedded PNGs', 'metal mask', 'review views', 'LOD chain']}


def main():
    (HERE / 'receipts').mkdir(exist_ok=True)
    (HERE / 'review/uv').mkdir(exist_ok=True)
    ledger = json.loads((HERE / 'ledger.json').read_text())
    report = HERE / 'receipts/validation.json'
    results = json.loads(report.read_text()) if report.exists() else {}
    selected = sys.argv[1:] or list(ledger)
    for icon in selected:
        assert icon in ledger
        results[icon] = check(icon)
        ledger[icon]['validation'] = f'receipts/validation.json#{icon}'
        ledger[icon]['review'] = {kind: [f'review/{kind}/{icon}_{view}.png'
                                        for view in ['top', 'threequarter', 'low', 'underside']]
                                  for kind in ['clay', 'textured']}
    report.write_text(json.dumps(results, indent=2) + '\n')
    (HERE / 'ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    print(f'Passed export checks for {len(selected)} owned icons')


if __name__ == '__main__':
    main()
