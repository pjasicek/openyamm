#!/usr/bin/env python3
"""Print a GLB's meshes, materials, triangles and bounds (node transforms applied, no skins).  glbinfo.py <glb>..."""
import json, struct, sys
import numpy as np

def load(path):
    raw = open(path, 'rb').read()
    n = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + n])
    bl = struct.unpack_from('<I', raw, 20 + n)[0]
    return doc, raw[28 + n:28 + n + bl]

def acc(doc, binary, i):
    a = doc['accessors'][i]; bv = doc['bufferViews'][a['bufferView']]
    comp = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a['componentType']]
    k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    off = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = bv.get('byteStride', 0)
    item = np.dtype(comp).itemsize * k
    if stride and stride != item:
        rows = [np.frombuffer(binary, comp, k, off + r * stride) for r in range(a['count'])]
        return np.array(rows)
    return np.frombuffer(binary, comp, a['count'] * k, off).reshape(a['count'], k)

def mat4(node):
    if 'matrix' in node: return np.array(node['matrix']).reshape(4, 4).T
    t = np.array(node.get('translation', [0, 0, 0])); s = np.array(node.get('scale', [1, 1, 1]))
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    r = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                  [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
    m = np.eye(4); m[:3, :3] = r * s; m[:3, 3] = t; return m

if __name__ == '__main__':
    for p in sys.argv[1:]:
        doc, binary = load(p)
        print('==', p, 'extras', doc.get('extras'))
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        def walk(i, m):
            global lo, hi
            node = doc['nodes'][i]; m = m @ mat4(node)
            if 'mesh' in node:
                mesh = doc['meshes'][node['mesh']]
                for pr in mesh['primitives']:
                    pos = acc(doc, binary, pr['attributes']['POSITION'])
                    w = (m @ np.c_[pos, np.ones(len(pos))].T).T[:, :3]
                    lo[:] = np.minimum(lo, w.min(0)); hi[:] = np.maximum(hi, w.max(0))
                    tris = doc['accessors'][pr['indices']]['count'] // 3 if 'indices' in pr else len(pos) // 3
                    print(f"  node {node.get('name')} mesh {mesh.get('name')} mat {pr.get('material')} tris {tris} attrs {list(pr['attributes'])}")
            for c in node.get('children', []): walk(c, m)
        for r in doc['scenes'][doc.get('scene', 0)]['nodes']: walk(r, np.eye(4))
        print('  bounds', lo.round(3), hi.round(3), 'size', (hi - lo).round(3))
        for i, mt in enumerate(doc.get('materials', [])):
            print('  mat', i, json.dumps(mt)[:300])
        for i, im in enumerate(doc.get('images', [])):
            print('  img', i, im.get('name'), im.get('mimeType'))
