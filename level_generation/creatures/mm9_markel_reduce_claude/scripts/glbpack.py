"""GLB helpers for the Banshee reduction: read/write, typed accessors, append, compaction of unreferenced accessors and
buffer views (images kept)."""
import copy, json, struct
import numpy as np
from bglbio import acc, SIZES, K  # noqa: F401


def read(path):
    raw = open(path, 'rb').read()
    n = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + n]), bytearray(raw[28 + n:])


def write(path, doc, binary):
    binary = bytearray(binary); binary += b'\0' * (-len(binary) % 4)
    doc['buffers'][0]['byteLength'] = len(binary)
    enc = json.dumps(doc, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(binary)) + struct.pack('<II', len(enc), 0x4e4f534a)
                + enc + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))


def raw_rows(doc, binary, i):
    """accessor as raw bytes per element (n, size) so any type is copied exactly"""
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    size = SIZES[a['componentType']] * K[a['type']]
    st = v.get('byteStride') or size
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.ndarray((a['count'], size), np.uint8, bytes(binary), off, (st, 1)).copy()


def append(doc, binary, template, rows, count=None):
    data = np.ascontiguousarray(rows).tobytes()
    binary += b'\0' * (-len(binary) % 4)
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary += data
    a = {k: v for k, v in template.items() if k not in ('bufferView', 'byteOffset', 'min', 'max', 'sparse')}
    a['bufferView'] = len(doc['bufferViews']) - 1
    a['count'] = count if count is not None else len(rows)
    doc['accessors'].append(a)
    return len(doc['accessors']) - 1


def set_minmax(doc, binary, i):
    a = doc['accessors'][i]
    if a['type'] == 'VEC3' and a['componentType'] == 5126:
        x = acc(doc, bytes(binary), i)
        a['min'] = x.min(0).astype(float).tolist(); a['max'] = x.max(0).astype(float).tolist()


def compact(doc, binary):
    used = set()
    for m in doc['meshes']:
        for p in m['primitives']:
            used |= set(p['attributes'].values()); used.add(p['indices'])
            for t in p.get('targets', []):
                used |= set(t.values())
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            used.add(s['inverseBindMatrices'])
    for a in doc.get('animations', []):
        for s in a['samplers']:
            used |= {s['input'], s['output']}
    amap = {o: n for n, o in enumerate(sorted(used))}
    views = sorted({doc['accessors'][i]['bufferView'] for i in used} |
                   {im['bufferView'] for im in doc.get('images', []) if 'bufferView' in im})
    vmap, nb, nv = {}, bytearray(), []
    for n, o in enumerate(views):
        v = copy.deepcopy(doc['bufferViews'][o]); s = v.get('byteOffset', 0)
        nb += b'\0' * (-len(nb) % 4); v['byteOffset'] = len(nb); nb += binary[s:s + v['byteLength']]
        nv.append(v); vmap[o] = n
    doc['accessors'] = [dict(doc['accessors'][o], bufferView=vmap[doc['accessors'][o]['bufferView']]) for o in sorted(used)]
    doc['bufferViews'] = nv
    for im in doc.get('images', []):
        if 'bufferView' in im:
            im['bufferView'] = vmap[im['bufferView']]
    for m in doc['meshes']:
        for p in m['primitives']:
            p['attributes'] = {k: amap[v] for k, v in p['attributes'].items()}; p['indices'] = amap[p['indices']]
    for s in doc.get('skins', []):
        if 'inverseBindMatrices' in s:
            s['inverseBindMatrices'] = amap[s['inverseBindMatrices']]
    for a in doc.get('animations', []):
        for s in a['samplers']:
            s['input'] = amap[s['input']]; s['output'] = amap[s['output']]
    return doc, nb
