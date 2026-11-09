#!/usr/bin/env python3
"""Play one clip of a GLB faster (user, round 3: "death - 2x faster"): every key time of the named animation is divided
by <factor>, in place when no other animation shares the time accessor, else on a new accessor. Meshes, skins and the
other clips stay byte-identical. Usage: clip_speed.py <in.glb> <clip> <factor> <out.glb>"""
import struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, clip, factor, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
doc, binary = read_glb(Path(src)); binary = bytearray(binary)
anim = next(a for a in doc['animations'] if a['name'] == clip)
others = {s['input'] for a in doc['animations'] if a is not anim for s in a['samplers']}
done = {}
for s in anim['samplers']:
    i = s['input']
    if i not in done:
        acc = doc['accessors'][i]; view = doc['bufferViews'][acc['bufferView']]
        assert acc['componentType'] == 5126 and acc['type'] == 'SCALAR' and 'byteStride' not in view
        t = [x / factor for x in struct.unpack(f'<{acc["count"]}f', accessor_bytes(doc, binary, i))]
        packed = struct.pack(f'<{len(t)}f', *t)
        if i in others:
            j = append_accessor(doc, binary, acc, packed)
        else:
            o = view.get('byteOffset', 0) + acc.get('byteOffset', 0); binary[o:o + len(packed)] = packed; j = i
        doc['accessors'][j]['min'], doc['accessors'][j]['max'] = [min(t)], [max(t)]
        done[i] = j
    s['input'] = done[i]
doc['buffers'][0]['byteLength'] = len(binary)
write_glb(Path(out), doc, bytes(binary))
print('SPED', clip, 'x', factor, '->', round(max(doc['accessors'][j]['max'][0] for j in done.values()), 4), 's,',
      len(done), 'time accessors', sum(i in others for i in done), 'shared')
