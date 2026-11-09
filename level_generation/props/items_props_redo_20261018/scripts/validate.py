"""Validate the exports: finite attributes, UVs in range, no degenerate triangles, grounded and centred,
three embedded 512 px PNG maps, single-sided material. Writes review/validation.json."""
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
R = P.parents[2]
sys.path.insert(0, str(R / 'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import array  # noqa: E402
sys.path.insert(0, str(R / 'tools'))
from link_static_model_lods import read_glb  # noqa: E402

report = {}
for icon in sys.argv[1:]:
    path = P / f'work/{icon}_export.glb'
    document, binary = read_glb(path)
    triangles, positions = 0, []
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            a = primitive['attributes']
            pos, nor, uv = (array(document, binary, a[key]) for key in ('POSITION', 'NORMAL', 'TEXCOORD_0'))
            idx = array(document, binary, primitive['indices']).reshape(-1, 3)
            assert all(np.isfinite(v).all() for v in (pos, nor, uv)), icon
            assert uv.min() >= -1e-5 and uv.max() <= 1.00001, icon
            area = np.linalg.norm(np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]]), axis=1)
            assert (area > 1e-12).all(), (icon, 'degenerate')
            triangles += len(idx)
            positions.append(pos)
    pos = np.concatenate(positions)
    low, high = pos.min(0), pos.max(0)
    assert abs(low[1]) < 1e-4 and max(abs(low[[0, 2]] + high[[0, 2]])) < 1e-4, (icon, low, high)
    assert len(document['images']) == 3 and len(document['materials']) == 1, icon
    assert not document['materials'][0].get('doubleSided', False), icon
    for image in document['images']:
        view = document['bufferViews'][image['bufferView']]
        picture = Image.open(io.BytesIO(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]))
        assert image['mimeType'] == 'image/png' and picture.size == (512, 512), icon
    report[icon] = {'triangles': triangles, 'export_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'gltf_extent': (high - low).round(4).tolist()}
    print(icon, triangles, 'ok')
(P / 'review/validation.json').write_text(json.dumps(report, indent=2) + '\n')
