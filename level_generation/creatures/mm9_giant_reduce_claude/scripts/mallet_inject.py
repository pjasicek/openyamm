#!/usr/bin/env python3
"""Put the rebuilt mallet into a LOD0 GLB: the GiantMallet_A primitive of the mesh node takes work/mallet_new.npz
(rigid on Xhammer, weight 1), and the four mallet images (gi_mallet_base, _normal, _orm, _region_mask) take
work/tex_new/*.png. Materials, variants mapping, samplers and every other primitive and image stay as they are; the
buffer is compacted. Usage: mallet_inject.py <in.glb> <out.glb> [mesh node, default Giant]"""
import copy
import struct
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, out = Path(sys.argv[1]), Path(sys.argv[2]); NODE = sys.argv[3] if len(sys.argv) > 3 else 'Giant'
doc, binary = read_glb(src); binary = bytearray(binary)
node = next(n for n in doc['nodes'] if n.get('name') == NODE)
joints = doc['skins'][node['skin']]['joints']; jx = [doc['nodes'][j]['name'] for j in joints].index('Xhammer')
d = np.load('work/mallet_new.npz')
P, N, UV, I = d['P'].astype(np.float32), d['N'].astype(np.float32), d['UV'].astype(np.float32), d['I'].astype(np.uint32)


def add(arr, ctype, atype, minmax=False, target=None):
    binary.extend(b'\0' * (-len(binary) % 4)); raw = arr.tobytes()
    view = {'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(raw)}
    if target:
        view['target'] = target
    doc['bufferViews'].append(view); binary.extend(raw)
    acc = {'bufferView': len(doc['bufferViews']) - 1, 'componentType': ctype, 'count': int(arr.shape[0]), 'type': atype}
    if minmax:
        acc['min'] = arr.min(0).tolist(); acc['max'] = arr.max(0).tolist()
    doc['accessors'].append(acc); return len(doc['accessors']) - 1


mesh = doc['meshes'][node['mesh']]
prim = next(p for p in mesh['primitives'] if doc['materials'][p['material']]['name'] == 'GiantMallet_A')
J = np.zeros((len(P), 4), np.uint16 if len(joints) > 255 else np.uint8); J[:, 0] = jx
W = np.zeros((len(P), 4), np.float32); W[:, 0] = 1
prim['attributes'] = {'POSITION': add(P, 5126, 'VEC3', True, 34962), 'NORMAL': add(N, 5126, 'VEC3', target=34962),
                      'TEXCOORD_0': add(UV, 5126, 'VEC2', target=34962),
                      'JOINTS_0': add(J, 5123 if J.dtype == np.uint16 else 5121, 'VEC4', target=34962),
                      'WEIGHTS_0': add(W, 5126, 'VEC4', target=34962)}
prim['indices'] = add(I.reshape(-1) if len(P) > 65535 else I.reshape(-1).astype(np.uint16), 5125 if len(P) > 65535 else 5123,
                      'SCALAR', target=34963)
for im in doc['images']:
    f = Path('work/tex_new') / f"{im.get('name')}.png"
    if f.exists():
        raw = f.read_bytes(); binary.extend(b'\0' * (-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(raw)}); binary.extend(raw)
        im['bufferView'] = len(doc['bufferViews']) - 1; im['mimeType'] = 'image/png'; print('IMAGE', im['name'], len(raw))
# compact: referenced accessors and views only
used_acc = set()
for m in doc['meshes']:
    for p in m['primitives']:
        used_acc |= set(p['attributes'].values()) | {p['indices']}
for s in doc['skins']:
    used_acc.add(s['inverseBindMatrices'])
for a in doc.get('animations', []):
    for s in a['samplers']:
        used_acc |= {s['input'], s['output']}
amap = {old: new for new, old in enumerate(sorted(used_acc))}
used_views = sorted({doc['accessors'][i]['bufferView'] for i in used_acc} | {im['bufferView'] for im in doc['images'] if 'bufferView' in im})
vmap, newbin, views = {}, bytearray(), []
for new, old in enumerate(used_views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); views.append(v); vmap[old] = new
doc['accessors'] = [dict(doc['accessors'][old], bufferView=vmap[doc['accessors'][old]['bufferView']]) for old in sorted(used_acc)]
doc['bufferViews'] = views
for im in doc['images']:
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
for m in doc['meshes']:
    for p in m['primitives']:
        p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
for s in doc['skins']:
    s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
for a in doc.get('animations', []):
    for s in a['samplers']:
        s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
write_glb(out, doc, bytes(newbin))
print('INJECTED mallet', len(I), 'triangles,', len(P), 'vertices;', f'{len(newbin) / 1e6:.1f} MB')
