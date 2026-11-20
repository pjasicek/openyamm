#!/usr/bin/env python3
"""Review-only GLB: a model with its attachment GLBs (actors.yml `attachments`, each placed at a node) merged in as
children of those nodes, so the viewer shows the Centaur's bow and quiver moving with the new gaits. Not for install.

    merge_attach.py <model.glb> <out.glb> <attachment.glb>=<node> [...]
"""
from pathlib import Path
import json
import struct
import sys


def read(path):
    data = Path(path).read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + length])
    rest = data[20 + length:]
    binary = rest[8:8 + struct.unpack_from('<I', rest, 0)[0]] if rest else b''
    return doc, bytearray(binary)


def write(path, doc, binary):
    text = json.dumps(doc, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    binary += b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(text) + 8 + len(binary)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, total) + struct.pack('<II', len(text), 0x4E4F534A) + text
                           + struct.pack('<II', len(binary), 0x004E4942) + binary)


def main():
    doc, binary = read(sys.argv[1])
    for item in sys.argv[3:]:
        file, node_name = item.split('=')
        add, add_bin = read(file)
        binary += b'\0' * (-len(binary) % 4)
        base = len(binary)
        binary += add_bin
        offsets = {key: len(doc.setdefault(key, [])) for key in
                   ('bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes')}
        for view in add.get('bufferViews', []):
            view['buffer'] = 0
            view['byteOffset'] = view.get('byteOffset', 0) + base
        for accessor in add.get('accessors', []):
            accessor['bufferView'] += offsets['bufferViews']
        for image in add.get('images', []):
            if 'bufferView' in image:
                image['bufferView'] += offsets['bufferViews']
        for texture in add.get('textures', []):
            if 'source' in texture:
                texture['source'] += offsets['images']
            if 'sampler' in texture:
                texture['sampler'] += offsets['samplers']
        for material in add.get('materials', []):
            text = json.dumps(material)
            material.clear()
            material.update(json.loads(text))
            for slot in ('baseColorTexture', 'metallicRoughnessTexture'):
                info = material.get('pbrMetallicRoughness', {}).get(slot)
                if info:
                    info['index'] += offsets['textures']
            for slot in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
                if slot in material:
                    material[slot]['index'] += offsets['textures']
        for mesh in add.get('meshes', []):
            for primitive in mesh['primitives']:
                primitive.pop('extensions', None)                    # variants: the default material
                primitive['attributes'] = {k: v + offsets['accessors'] for k, v in primitive['attributes'].items()}
                if 'indices' in primitive:
                    primitive['indices'] += offsets['accessors']
                if 'material' in primitive:
                    primitive['material'] += offsets['materials']
        for node in add.get('nodes', []):
            if 'mesh' in node:
                node['mesh'] += offsets['meshes']
            if 'children' in node:
                node['children'] = [c + offsets['nodes'] for c in node['children']]
            node['name'] = node.get('name', '') + '_attached'
        for key in offsets:
            doc[key] += add.get(key, [])
        target = next(i for i, n in enumerate(doc['nodes'][:offsets['nodes']]) if n.get('name') == node_name)
        doc['nodes'][target].setdefault('children', []).extend(r + offsets['nodes'] for r in add['scenes'][0]['nodes'])
    doc['buffers'] = [{'byteLength': len(binary) + (-len(binary) % 4)}]
    write(sys.argv[2], doc, binary)
    print('wrote', sys.argv[2])


if __name__ == '__main__':
    main()
