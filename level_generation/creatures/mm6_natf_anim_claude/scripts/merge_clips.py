#!/usr/bin/env python3
"""Replace named animations of a runtime GLB with those of a clips GLB from the same rig (export_clips.py): channels
are matched by node name; the joints' rest transforms must agree (checked, skirt cage bones excepted: they are no
longer weighted). Usage: merge_clips.py <runtime.glb> <clips.glb> <out.glb> <clip> [...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

src, clips, out, names = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4:]
doc, binary = read_glb(src); binary = bytearray(binary)
cdoc, cbin = read_glb(clips)
index = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
cnodes = cdoc['nodes']
for n in cnodes:
    name = n.get('name', '')
    if name in index and name.startswith('B_'):
        d = doc['nodes'][index[name]]
        for key, default in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1])):
            x, y = np.array(n.get(key, default)), np.array(d.get(key, default))
            if key == 'rotation' and np.dot(x, y) < 0:
                y = -y
            assert np.abs(x - y).max() < 1e-3, (name, key)
for name in names:
    canim = next(x for x in cdoc['animations'] if x['name'] == name)
    samplers, channels, smap = [], [], {}
    for ch in canim['channels']:
        tname = cnodes[ch['target']['node']].get('name')
        if tname not in index:
            continue
        si = ch['sampler']
        if si not in smap:
            s = canim['samplers'][si]
            smap[si] = len(samplers)
            samplers.append({'input': append_accessor(doc, binary, cdoc['accessors'][s['input']], accessor_bytes(cdoc, cbin, s['input'])),
                             'output': append_accessor(doc, binary, cdoc['accessors'][s['output']], accessor_bytes(cdoc, cbin, s['output'])),
                             'interpolation': s.get('interpolation', 'LINEAR')})
        channels.append({'sampler': smap[si], 'target': {'node': index[tname], 'path': ch['target']['path']}})
    new = {'name': name, 'samplers': samplers, 'channels': channels}
    pos = next((i for i, x in enumerate(doc['animations']) if x['name'] == name), None)
    if pos is None:
        doc['animations'].append(new)
    else:
        doc['animations'][pos] = new
    print('MERGED', name, len(channels), 'channels')
write_glb(out, doc, bytes(binary))
