#!/usr/bin/env python3
"""Review-only GLB: the body with its attachments baked in as extra primitives skinned 100 % to their node, in a
flat colour, so Blender and the browser viewer show props moving with the clips. Never installed.

    review_glb.py <body.glb> <out.glb> node=attachment.glb[:r,g,b] [...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402


def append_raw(glb, values, component, kind):
    data = np.ascontiguousarray(values)
    glb.bin += b'\0' * (-len(glb.bin) % 4)
    views = glb.json['bufferViews']
    views.append({'buffer': 0, 'byteOffset': len(glb.bin), 'byteLength': data.nbytes})
    glb.bin += data.tobytes()
    glb.json['accessors'].append({'bufferView': len(views) - 1, 'componentType': component, 'count': len(data),
                                  'type': kind})
    glb.json['buffers'][0]['byteLength'] = len(glb.bin)
    return len(glb.json['accessors']) - 1


def main():
    body = glb_pose.Glb(sys.argv[1])
    model = glb_pose.Model(body)
    names = [n['name'] for n in body.json['nodes']]
    mesh_node = next(n for n in body.json['nodes'] if 'mesh' in n and 'skin' in n)
    mesh = body.json['meshes'][mesh_node['mesh']]
    for item in sys.argv[3:]:
        node, rest = item.split('=', 1)
        path, _, colour = rest.partition(':')
        rgb = [float(v) for v in colour.split(',')] if colour else [0.55, 0.55, 0.6]
        att = glb_pose.Model(glb_pose.Glb(path))
        joint = model.joints.index(names.index(node))
        ibm = model.inverse_binds[joint]
        for prim in att.primitives:
            p = prim['positions']
            bind = (np.linalg.inv(ibm) @ np.c_[p, np.ones(len(p))].T).T[:, :3]
            pos = body.append_accessor(bind, 'VEC3')
            joints = append_raw(body, np.tile(np.array([joint, 0, 0, 0], np.uint16), (len(p), 1)), 5123, 'VEC4')
            weights = body.append_accessor(np.tile([1.0, 0, 0, 0], (len(p), 1)), 'VEC4')
            idx = append_raw(body, prim['triangles'].astype(np.uint32).ravel(), 5125, 'SCALAR')
            body.json['materials'].append({'name': f'review_{node}', 'pbrMetallicRoughness': {
                'baseColorFactor': rgb + [1.0], 'metallicFactor': 0.0, 'roughnessFactor': 0.7}})
            mesh['primitives'].append({'attributes': {'POSITION': pos, 'JOINTS_0': joints, 'WEIGHTS_0': weights},
                                       'indices': idx, 'material': len(body.json['materials']) - 1})
    body.write(sys.argv[2])
    print('wrote', sys.argv[2])


if __name__ == '__main__':
    main()
