#!/usr/bin/env python3
"""Check that two GLBs hold the same content apart from the named animations: every accessor reached from meshes, skins and
other animations, every image, and the JSON of nodes/meshes/materials/skins/textures/samplers/extensions compare by
value (buffer layout may differ after compaction). Usage: diff_except.py <a.glb> <b.glb> [animation[,animation...]=Attack]"""
import json, struct, sys, hashlib


def read(p):
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; d = json.loads(b[20:20 + n])
    o = 20 + n; m = struct.unpack('<I', b[o:o + 4])[0]; return d, b[o + 8:o + 8 + m]


def view(d, bin_, i):
    v = d['bufferViews'][i]; s = v.get('byteOffset', 0); return bin_[s:s + v['byteLength']]


def acc(d, bin_, i):
    a = dict(d['accessors'][i]); raw = view(d, bin_, a.pop('bufferView')) if 'bufferView' in d['accessors'][i] else b''
    a.pop('byteOffset', None); off = d['accessors'][i].get('byteOffset', 0)
    return json.dumps(a, sort_keys=True), hashlib.sha256(raw[off:]).hexdigest()


def resolve(d, bin_, obj):
    """Replace accessor/image indices by their content digests."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ('indices', 'input', 'output', 'inverseBindMatrices') and isinstance(v, int):
                out[k] = acc(d, bin_, v)
            elif k == 'attributes' or k == 'targets':
                out[k] = resolve_attrs(d, bin_, v)
            else:
                out[k] = resolve(d, bin_, v)
        return out
    if isinstance(obj, list):
        return [resolve(d, bin_, x) for x in obj]
    return obj


def resolve_attrs(d, bin_, v):
    if isinstance(v, list):
        return [resolve_attrs(d, bin_, x) for x in v]
    return {k: acc(d, bin_, i) for k, i in v.items()}


a, ba = read(sys.argv[1]); b, bb = read(sys.argv[2]); skip = set((sys.argv[3] if len(sys.argv) > 3 else 'Attack').split(','))
bad = []
for key in ('asset', 'scene', 'scenes', 'nodes', 'meshes', 'materials', 'skins', 'textures', 'samplers',
            'extensionsUsed', 'extensionsRequired', 'extensions', 'cameras'):
    if resolve(a, ba, a.get(key)) != resolve(b, bb, b.get(key)):
        bad.append(key)
ia = [hashlib.sha256(view(a, ba, im['bufferView'])).hexdigest() for im in a.get('images', [])]
ib = [hashlib.sha256(view(b, bb, im['bufferView'])).hexdigest() for im in b.get('images', [])]
if ia != ib or [dict(im, bufferView=0) for im in a.get('images', [])] != [dict(im, bufferView=0) for im in b.get('images', [])]:
    bad.append('images')
an = {x['name']: x for x in a['animations']}; bn = {x['name']: x for x in b['animations']}
if list(an) != list(bn):
    bad.append('animation names')
for name in an:
    if name not in skip and resolve(a, ba, an[name]) != resolve(b, bb, bn.get(name)):
        bad.append('animation ' + name)
print('DIFF_EXCEPT', sorted(skip), 'identical' if not bad else bad, '| skipped clips equal:',
      {n: resolve(a, ba, an[n]) == resolve(b, bb, bn[n]) for n in sorted(skip)})
