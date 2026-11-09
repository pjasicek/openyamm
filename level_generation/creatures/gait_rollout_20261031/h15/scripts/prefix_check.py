#!/usr/bin/env python3
"""The export keeps the input intact: its binary chunk starts with the input's, every input accessor, buffer view,
mesh, skin, material and animation is unchanged, and only animations are appended.  prefix_check.py <in> <out>"""
import json
import struct
import sys


def read(path):
    b = open(path, 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n])
    o = 20 + n
    m = struct.unpack('<I', b[o:o + 4])[0]
    return j, b[o + 8:o + 8 + m]


a, ab = read(sys.argv[1])
b, bb = read(sys.argv[2])
ok = bb[:len(ab)] == ab
for key in ('nodes', 'meshes', 'skins', 'materials', 'textures', 'images', 'samplers', 'extensions'):
    ok &= a.get(key) == b.get(key)
for key in ('accessors', 'bufferViews', 'animations'):
    ok &= b[key][:len(a[key])] == a[key]
new = [x['name'] for x in b['animations'][len(a['animations']):]]
print('PREFIX', 'ok' if ok else 'CHANGED', 'appended', new)
