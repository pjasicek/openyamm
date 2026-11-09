#!/usr/bin/env python3
"""Triangles per mesh of a GLB (LOD0-3 and shadows). Usage: lod_counts.py <glb>..."""
import json, struct, sys
for p in sys.argv[1:]:
    b = open(p, 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n])
    print(p.split('/')[-1], {m['name']: sum(j['accessors'][q['indices']]['count'] // 3 for q in m['primitives']) for m in j['meshes']})
