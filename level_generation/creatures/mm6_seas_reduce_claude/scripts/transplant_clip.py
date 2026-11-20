#!/usr/bin/env python3
"""Replace one animation's channel data in a runtime GLB with the same clip from a donor GLB (attack_donor.py),
matched by node name and path; every other byte of the target stays. --check only prints the largest difference per
path (validates that the donor export matches the target's own clip before a changed clip is transplanted).
Usage: transplant_clip.py <target.glb> <donor.glb> <clip> [<out.glb> | --check]"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

target, donor, clip, out = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
td, tb = read_glb(target); dd, db = read_glb(donor); tb = bytearray(tb)
ta = next(a for a in td['animations'] if a['name'] == clip); da = next(a for a in dd['animations'] if a['name'] == clip)
dch = {(dd['nodes'][c['target']['node']]['name'], c['target']['path']): da['samplers'][c['sampler']] for c in da['channels']}
floats = lambda doc, b, i: struct.unpack(f'<{len(accessor_bytes(doc, b, i)) // 4}f', accessor_bytes(doc, b, i))
worst = {}
for c in ta['channels']:
    key = (td['nodes'][c['target']['node']]['name'], c['target']['path'])
    src = dch[key]; dst = ta['samplers'][c['sampler']]
    if out == '--check':
        a, b = floats(td, tb, dst['output']), floats(dd, db, src['output'])
        d = max(abs(x - y) for x, y in zip(a, b)) if len(a) == len(b) else float('inf')
        worst[key[1]] = max(worst.get(key[1], 0.0), d)
        continue
    for k in ('input', 'output'):
        dst[k] = append_accessor(td, tb, dd['accessors'][src[k]], accessor_bytes(dd, db, src[k]))
    dst['interpolation'] = src.get('interpolation', 'LINEAR')
if out == '--check':
    print('CHECK', clip, {k: round(v, 6) for k, v in worst.items()})
else:
    write_glb(Path(out), td, bytes(tb)); print('TRANSPLANTED', clip, len(ta['channels']), 'channels ->', out)
