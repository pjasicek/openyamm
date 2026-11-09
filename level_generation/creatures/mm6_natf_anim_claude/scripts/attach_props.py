#!/usr/bin/env python3
"""Viewer only: copy a static prop GLB's full-detail mesh (with its materials and images) under the joint node that
carries it, so three.js shows the held item with the clips. Usage: attach_props.py <body glb> <out glb> <prop glb>:<joint> [...]"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

body, out, specs = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
doc, binary = read_glb(body); binary = bytearray(binary)
names = [n.get('name') for n in doc['nodes']]
for spec in specs:
    path, joint = spec.rsplit(':', 1)
    pd, pb = read_glb(Path(path))
    pnode = next(n for n in pd['nodes'] if 'mesh' in n); pmesh = pd['meshes'][pnode['mesh']]
    imap, tmap, mmap = {}, {}, {}
    for prim in pmesh['primitives']:
        mi = prim['material']
        if mi in mmap:
            continue
        mat = copy.deepcopy(pd['materials'][mi])
        def tex(ref):
            t = ref['index']
            if t not in tmap:
                tt = copy.deepcopy(pd['textures'][t]); s = tt['source']
                if s not in imap:
                    im = copy.deepcopy(pd['images'][s]); v = pd['bufferViews'][im['bufferView']]; st = v.get('byteOffset', 0)
                    binary.extend(b'\0' * (-len(binary) % 4)); doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': v['byteLength']})
                    binary.extend(pb[st:st + v['byteLength']]); im['bufferView'] = len(doc['bufferViews']) - 1
                    doc['images'].append(im); imap[s] = len(doc['images']) - 1
                tt['source'] = imap[s]; tt.pop('sampler', None); doc['textures'].append(tt); tmap[t] = len(doc['textures']) - 1
            ref['index'] = tmap[t]
        pbr = mat.get('pbrMetallicRoughness', {})
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            if key in pbr: tex(pbr[key])
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in mat: tex(mat[key])
        mat.pop('extras', None); mat.pop('extensions', None)
        doc['materials'].append(mat); mmap[mi] = len(doc['materials']) - 1
    prims = []
    for prim in pmesh['primitives']:
        attrs = {k: append_accessor(doc, binary, pd['accessors'][v], accessor_bytes(pd, pb, v)) for k, v in prim['attributes'].items()
                 if k in ('POSITION', 'NORMAL', 'TEXCOORD_0')}
        prims.append({'attributes': attrs, 'indices': append_accessor(doc, binary, pd['accessors'][prim['indices']], accessor_bytes(pd, pb, prim['indices'])),
                      'material': mmap[prim['material']]})
    doc['meshes'].append({'name': pmesh.get('name', 'prop'), 'primitives': prims})
    doc['nodes'].append({'name': pnode.get('name', 'prop') + '_viewer', 'mesh': len(doc['meshes']) - 1})
    doc['nodes'][names.index(joint)].setdefault('children', []).append(len(doc['nodes']) - 1)
    print('ATTACHED', path, 'to', joint)
write_glb(out, doc, bytes(binary))
