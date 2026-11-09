"""Link and validate the nine closed-coin piles before installation."""
import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from link_static_model_lods import link, read_glb, write_glb

spec = importlib.util.spec_from_file_location('winding', ROOT / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py')
winding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(winding)
ownership = json.loads((PROJECT / 'ownership.json').read_text())
receipts = json.loads((PROJECT / 'work/build_receipts.json').read_text())
assert {r['icon'] for r in ownership} == set(receipts)
report = {}
for row in ownership:
    icon = row['icon']
    raw = PROJECT / 'work/unlinked' / (icon + '_export.glb')
    path = PROJECT / 'work/exports' / raw.name
    if not path.exists() or path.stat().st_mtime < raw.stat().st_mtime:
        document, binary = read_glb(raw)
        link(document)
        write_glb(path, document, binary)
    g, binary = read_glb(path)
    assert len(g['nodes']) == 1 and len(g['materials']) == 1 and len(g['images']) == 3
    node = g['nodes'][0]
    assert not any(k in node for k in ['translation', 'rotation', 'scale', 'matrix'])
    pbr = g['materials'][0]['pbrMetallicRoughness']
    assert 'baseColorTexture' in pbr and 'metallicRoughnessTexture' in pbr and 'normalTexture' in g['materials'][0]
    base = node['mesh']
    order = [base] + g['meshes'][base]['extras']['openyamm_lods']
    counts = []
    for mesh_id in order:
        mesh = g['meshes'][mesh_id]
        assert len(mesh['primitives']) == 1
        primitive = mesh['primitives'][0]
        attr = primitive['attributes']
        pos = winding.array(g, binary, attr['POSITION'])
        normal = winding.array(g, binary, attr['NORMAL'])
        uv = winding.array(g, binary, attr['TEXCOORD_0'])
        indices = winding.array(g, binary, primitive['indices']).reshape(-1, 3)
        assert np.isfinite(pos).all() and np.isfinite(normal).all() and np.isfinite(uv).all()
        assert np.allclose(np.linalg.norm(normal, axis=1), 1, atol=.005)
        assert uv.min() >= 0 and uv.max() <= 1
        a, b, c = (pos[indices[:, k]] for k in range(3))
        assert (np.linalg.norm(np.cross(b-a, c-a), axis=1) > 1e-12).all()
        u, v, w = (uv[indices[:, k]] for k in range(3))
        d, e = v-u, w-u
        assert (np.abs(d[:, 0]*e[:, 1]-d[:, 1]*e[:, 0]) > 1e-10).all()
        keys = [tuple(np.round(point, 7)) for point in pos]
        parts = winding.components(indices, keys)
        assert len(parts) == receipts[icon]['coins'], (icon, len(parts))
        for part in parts:
            pa, pb, pc = (pos[indices[part, k]] for k in range(3))
            assert np.einsum('ij,ij->i', pa, np.cross(pb, pc)).sum() / 6 > 0
        lo, hi = pos.min(0), pos.max(0)
        assert abs(lo[1]) < 1e-6 and abs(lo[0]+hi[0]) < 1e-6 and abs(lo[2]+hi[2]) < 1e-6
        assert np.ptp(pos[:, 2]) >= np.ptp(pos[:, 0]) - 1e-6
        counts.append(len(indices))
    assert counts == receipts[icon]['triangles'] and all(a>b for a,b in zip(counts,counts[1:]))
    assert counts[0] < 15000
    for image in g['images']:
        assert image.get('mimeType') == 'image/png' and 'uri' not in image
        view = g['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        png = Image.open(io.BytesIO(binary[start:start+view['byteLength']]))
        assert png.size == (512, 512)
        png.verify()
    with contextlib.redirect_stdout(io.StringIO()):
        assert winding.check(path) == 0
    report[icon] = dict(status='passed', coins=receipts[icon]['coins'], triangles=counts,
                        closed_coin_components=True, no_mound=True, pbr=True, normal_map=True,
                        uv_area=True, grounding=True, normals=True)
(PROJECT / 'work/validation.json').write_text(json.dumps(report, indent=2)+'\n')
print('PASS: all nine piles; closed coins, normals, UVs, PBR maps, grounding and four LODs.')
