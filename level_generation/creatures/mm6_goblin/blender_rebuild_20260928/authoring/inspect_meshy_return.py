"""Archive and inspect the returned texture GLB before transferring any materials."""
import hashlib
import io
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image

from check_glb import Glb, ROOT

SOURCE = Path('/home/pjasicek/Downloads/Meshy_AI_mm6_goblin_texturing_0928122704_texture.glb')
OUTPUT = ROOT / 'textures/meshy_20260928'


def node_matrix(node):
    if 'matrix' in node:
        return np.asarray(node['matrix'], dtype=float).reshape(4, 4).T
    matrix = np.identity(4)
    x, y, z, w = node.get('rotation', (0, 0, 0, 1))
    matrix[:3, :3] = np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]) @ np.diag(node.get('scale', (1, 1, 1)))
    matrix[:3, 3] = node.get('translation', (0, 0, 0))
    return matrix


def collect(glb):
    positions, normals, uvs, indices = [], [], [], []
    nodes = glb.json['nodes']
    parents = {child: i for i, node in enumerate(nodes) for child in node.get('children', [])}
    def world(index):
        local = node_matrix(nodes[index])
        return world(parents[index]) @ local if index in parents else local
    for index, node in enumerate(nodes):
        if 'mesh' not in node:
            continue
        transform = world(index)
        normal_transform = np.linalg.inv(transform[:3, :3]).T
        for primitive in glb.json['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            pos = np.array(glb.accessor(attrs['POSITION']))
            normal = np.array(glb.accessor(attrs['NORMAL'])) @ normal_transform.T
            normal /= np.linalg.norm(normal, axis=1, keepdims=True)
            indices.extend(np.array(glb.accessor(primitive['indices'])).reshape(-1, 3) + len(positions))
            positions.extend((np.column_stack((pos, np.ones(len(pos)))) @ transform.T)[:, :3])
            normals.extend(normal)
            uvs.extend(glb.accessor(attrs['TEXCOORD_0']))
    return tuple(np.array(values) for values in (positions, normals, uvs, indices))


def inspect():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    archive = OUTPUT / 'meshy_return.glb'
    if archive.exists():
        assert archive.read_bytes() == SOURCE.read_bytes(), 'Archived input differs; preserve revisions separately.'
    else:
        shutil.copy2(SOURCE, archive)
    original = Glb(ROOT / 'delivery/mm6_goblin_texturing.glb')
    returned = Glb(archive)
    a, na, ua, ia = collect(original)
    b, nb, ub, ib = collect(returned)
    assert np.array_equal(ia, ib), 'Triangle order/connectivity changed.'
    assert np.array_equal(ua, ub), 'UVs changed; direct material transfer is unsafe.'
    position_error = float(np.max(np.linalg.norm(a-b, axis=1)))
    normal_error = float(np.max(np.linalg.norm(na-nb, axis=1)))
    assert position_error < .000002, position_error
    assert normal_error < .00001, normal_error
    j = returned.json
    assert len(j['materials']) == 1 and not j.get('skins') and not j.get('animations')
    material = j['materials'][0]
    slots = {'base_color': material['pbrMetallicRoughness']['baseColorTexture'],
             'metallic_roughness': material['pbrMetallicRoughness']['metallicRoughnessTexture'],
             'normal': material['normalTexture']}
    maps = []
    for role, slot in slots.items():
        assert slot.get('texCoord', 0) == 0 and not slot.get('extensions')
        texture = j['textures'][slot['index']]
        info = j['images'][texture['source']]
        view = j['bufferViews'][info['bufferView']]
        start = view.get('byteOffset', 0)
        raw = returned.binary[start:start + view['byteLength']]
        extension = {'image/jpeg': '.jpg', 'image/png': '.png'}[info['mimeType']]
        path = OUTPUT / (role + extension)
        path.write_bytes(raw)
        image = Image.open(io.BytesIO(raw))
        maps.append({'role': role, 'file': path.name, 'dimensions': list(image.size),
                     'mime_type': info['mimeType'], 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    report = {'status': 'pass', 'source': str(SOURCE), 'source_sha256': hashlib.sha256(returned.raw).hexdigest(),
              'input_sha256': hashlib.sha256(original.raw).hexdigest(), 'triangles': len(ia),
              'split_vertices': len(a), 'connectivity_and_vertex_order_identical': True, 'uvs_bit_identical': True,
              'maximum_world_position_error_m': position_error, 'maximum_world_normal_vector_error': normal_error,
              'mesh_parts_before': len(original.json['meshes']), 'mesh_parts_returned': len(j['meshes']),
              'maps': maps, 'material': material,
              'transfer': 'Use the returned PBR textures on the existing authored parts, UVs and rig.'}
    (OUTPUT / 'import_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    inspect()
