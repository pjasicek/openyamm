#!/usr/bin/env python3
"""Merge an attachment GLB into a carrier GLB as a mesh node child of a named joint (for viewer composites and
offline previews; the game binds attachments by `attachments: {model, node}` instead).

Usage: merge_attachment.py <carrier.glb> <attachment.glb> <joint> <out.glb> [<attachment.glb> <joint> ...]"""
import json, struct, sys
from pathlib import Path


def read(path):
    data = Path(path).read_bytes()
    off, doc, binary = 12, None, b''
    while off < len(data):
        length, kind = struct.unpack_from('<II', data, off)
        chunk = data[off + 8: off + 8 + length]
        if kind == 0x4E4F534A:
            doc = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        off += 8 + length
    return doc, bytearray(binary)


def write(path, doc, binary):
    js = json.dumps(doc, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4); binary += b'\0' * (-len(binary) % 4)
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(binary))
    out += struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(binary), 0x004E4942) + binary
    Path(path).write_bytes(out)


doc, binary = read(sys.argv[1])
out = sys.argv[4]
pairs = [(sys.argv[2], sys.argv[3])] + list(zip(sys.argv[5::2], sys.argv[6::2]))
for att_path, joint in pairs:
    att, ab = read(att_path)
    base_off = len(binary) + (-len(binary) % 4)
    binary += b'\0' * (-len(binary) % 4) + ab
    o = {k: len(doc.get(k, [])) for k in ('bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials',
                                         'meshes')}
    for bv in att.get('bufferViews', []):
        bv = dict(bv); bv['buffer'] = 0; bv['byteOffset'] = bv.get('byteOffset', 0) + base_off
        doc.setdefault('bufferViews', []).append(bv)
    for acc in att.get('accessors', []):
        acc = dict(acc); acc['bufferView'] += o['bufferViews']; doc.setdefault('accessors', []).append(acc)
    for im in att.get('images', []):
        im = dict(im)
        if 'bufferView' in im:
            im['bufferView'] += o['bufferViews']
        doc.setdefault('images', []).append(im)
    for s in att.get('samplers', []):
        doc.setdefault('samplers', []).append(s)
    for t in att.get('textures', []):
        t = dict(t)
        if 'source' in t:
            t['source'] += o['images']
        if 'sampler' in t:
            t['sampler'] += o['samplers']
        doc.setdefault('textures', []).append(t)

    def fix(x):
        if isinstance(x, dict):
            return {k: (v + o['textures'] if k == 'index' and isinstance(v, int) else fix(v)) for k, v in x.items()}
        if isinstance(x, list):
            return [fix(v) for v in x]
        return x
    for m in att.get('materials', []):
        doc.setdefault('materials', []).append(fix(m))
    for me in att.get('meshes', []):
        me = json.loads(json.dumps(me))
        for p in me['primitives']:
            p['attributes'] = {k: v + o['accessors'] for k, v in p['attributes'].items()}
            if 'indices' in p:
                p['indices'] += o['accessors']
            if 'material' in p:
                p['material'] += o['materials']
            p.pop('extensions', None)
        doc['meshes'].append(me)
    names = [n.get('name') for n in doc['nodes']]
    parent = names.index(joint)
    for k, n in enumerate(att['nodes']):
        if 'mesh' in n:
            node = {'name': n.get('name', 'att') + '_att', 'mesh': n['mesh'] + o['meshes']}
            for key in ('translation', 'rotation', 'scale'):
                if key in n:
                    node[key] = n[key]
            doc['nodes'].append(node)
            doc['nodes'][parent].setdefault('children', []).append(len(doc['nodes']) - 1)
doc['buffers'] = [{'byteLength': len(binary)}]
write(out, doc, binary)
print('MERGED', out)
