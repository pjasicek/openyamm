#!/usr/bin/env python3
"""The export only appends: the input's binary chunk is a byte-identical prefix of the export's, every JSON key other
than animations/accessors/bufferViews/buffers is equal, the input's animations, accessors and bufferViews are an
unchanged prefix of the export's, and the new animations are listed.  identity_check.py <in.glb> <out.glb>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

a, b = glb_pose.Glb(sys.argv[1]), glb_pose.Glb(sys.argv[2])
ok = bytes(b.bin[:len(a.bin)]) == bytes(a.bin)
for key in set(a.json) | set(b.json):
    if key in ('animations', 'accessors', 'bufferViews', 'buffers'):
        n = len(a.json.get(key, []))
        same = a.json.get(key, []) == b.json.get(key, [])[:n] if key != 'buffers' else True
    else:
        same = a.json.get(key) == b.json.get(key)
    if not same:
        print('DIFFERS', key)
        ok = False
new = [x['name'] for x in b.json['animations'][len(a.json['animations']):]]
print(f"{'IDENTICAL PREFIX' if ok else 'CHANGED'}: bin {len(a.bin)} -> {len(b.bin)} bytes, new clips {new}")
sys.exit(0 if ok else 1)
