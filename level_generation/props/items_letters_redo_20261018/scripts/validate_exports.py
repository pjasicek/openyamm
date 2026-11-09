"""Static checks of every export: three embedded 512 px PNG maps, single-sided material, finite attributes, no
degenerate triangles, footprint centred and lowest point at zero; writes review/validation.json.
Usage: python3 validate_exports.py <icon ...>"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'level_generation/decorations/mm8_3d/animated/scripts'))
from check_winding import array  # noqa: E402

report = {}
for icon in sys.argv[1:]:
    path = P / 'work/exports' / f'item_{icon}_export.glb'
    data = path.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + length])
    binary = data[20 + length + 8:]
    positions, triangles = [], 0
    for mesh in document['meshes']:
        for primitive in mesh['primitives']:
            p = array(document, binary, primitive['attributes']['POSITION'])
            n = array(document, binary, primitive['attributes']['NORMAL'])
            uv = array(document, binary, primitive['attributes']['TEXCOORD_0'])
            index = array(document, binary, primitive['indices']).reshape(-1, 3)
            assert np.isfinite(p).all() and np.isfinite(n).all() and np.isfinite(uv).all(), icon
            area = np.linalg.norm(np.cross(p[index[:, 1]] - p[index[:, 0]], p[index[:, 2]] - p[index[:, 0]]), axis=1)
            assert (area > 1e-12).all(), (icon, 'degenerate')
            triangles += len(index)
            positions.append(p)
    p = np.concatenate(positions)
    low, high = p.min(0), p.max(0)
    assert abs(low[1]) < 1e-4 and max(abs(low[[0, 2]] + high[[0, 2]])) < 1e-4, (icon, low, high)
    assert len(document['images']) == 3, icon
    for image in document['images']:
        view = document['bufferViews'][image['bufferView']]
        picture = Image.open(io.BytesIO(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]))
        assert image['mimeType'] == 'image/png' and picture.size == (512, 512), (icon, picture.size)
    assert all(not m.get('doubleSided') for m in document['materials']), (icon, 'double-sided')
    assert 0 < triangles <= 3200, (icon, triangles)
    report[icon] = {'triangles': triangles, 'size_gltf': (high - low).round(4).tolist(), 'materials': len(document['materials'])}
    print(icon, report[icon])
(P / 'review/validation.json').write_text(json.dumps(report, indent=2) + '\n')
