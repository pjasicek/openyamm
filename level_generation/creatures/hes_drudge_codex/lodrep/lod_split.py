"""Write one GLB per colour LOD level: every node whose mesh lists openyamm_lods draws that level instead.

Usage: lod_split.py <out_dir> <glb...>  ->  <out_dir>/<stem>/lod<N>.glb and a manifest line per model on stdout.
"""
import json
import os
import struct
import sys


def read(path):
    data = open(path, 'rb').read()
    jlen = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + jlen])
    return gltf, data[20 + jlen:]


def write(path, gltf, rest):
    text = json.dumps(gltf, separators=(',', ':')).encode()
    text += b' ' * ((4 - len(text) % 4) % 4)
    total = 12 + 8 + len(text) + len(rest)
    with open(path, 'wb') as out:
        out.write(struct.pack('<III', 0x46546C67, 2, total))
        out.write(struct.pack('<II', len(text), 0x4E4F534A))
        out.write(text)
        out.write(rest)


out_dir = sys.argv[1]
for path in sys.argv[2:]:
    gltf, rest = read(path)
    meshes = gltf.get('meshes', [])
    chains = {i: (m.get('extras') or {}).get('openyamm_lods') for i, m in enumerate(meshes)}
    chains = {i: c for i, c in chains.items() if c}
    if not chains:
        continue
    levels = 1 + max(len(c) for c in chains.values())
    stem = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(os.path.join(out_dir, stem), exist_ok=True)
    for level in range(levels):
        copy = json.loads(json.dumps(gltf))
        for node in copy.get('nodes', []):
            chain = chains.get(node.get('mesh'))
            if chain and level > 0:
                node['mesh'] = chain[min(level, len(chain)) - 1]
        write(os.path.join(out_dir, stem, f'lod{level}.glb'), copy, rest)
    print(f'{stem}\t{levels}\t{path}')
