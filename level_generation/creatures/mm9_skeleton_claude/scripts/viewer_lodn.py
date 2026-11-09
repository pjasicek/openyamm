#!/usr/bin/env python3
"""A viewer copy of a tier GLB that draws LOD1 as its main mesh. Args: <in glb> <out glb>"""
import json, struct, sys
d = open(sys.argv[1], 'rb').read(); n = struct.unpack_from('<I', d, 12)[0]; j = json.loads(d[20:20 + n]); rest = d[20 + n:]
node = next(x for x in j['nodes'] if x.get('mesh') == 0)
lod1 = j['meshes'][0]['extras']['openyamm_lods'][int(sys.argv[3])]
node['mesh'] = lod1
for m in j['materials']:
    pass
for p in j['meshes'][lod1]['primitives']:
    pass
enc = json.dumps(j, separators=(',', ':')).encode(); enc += b' ' * (-len(enc) % 4)
open(sys.argv[2], 'wb').write(struct.pack('<III', 0x46546C67, 2, 20 + len(enc) + len(rest)) + struct.pack('<II', len(enc), 0x4E4F534A) + enc + rest)
