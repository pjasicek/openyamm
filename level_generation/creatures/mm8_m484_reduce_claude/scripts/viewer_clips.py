#!/usr/bin/env python3
"""Review-viewer files for the one-handed rework: the viewer needs every clip in every model with one duration, so
- the installed rows (`*_r100.glb`, copies of mm8_m484_claude/review/viewer) get the installed two-handed attack as
  `Attack2H`, the new one-handed Attack / Cast, and lose AttackOneHand;
- the new rows (`*_r73oh.glb`) get the installed two-handed attack as `Attack2H` too.
Clips are copied by node name, so node order may differ between the files.
Usage: viewer_clips.py <installed tier glb> <new tier glb> <out installed> <out new>"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402


def copy_clip(sdoc, sbin, name, ddoc, dbin, new_name):
    a = next(x for x in sdoc['animations'] if x['name'] == name)
    dn = {n.get('name'): k for k, n in enumerate(ddoc['nodes'])}
    out = {'name': new_name, 'channels': [], 'samplers': []}
    for ch in a['channels']:
        s = a['samplers'][ch['sampler']]; node = sdoc['nodes'][ch['target']['node']].get('name')
        if node not in dn:
            continue
        ns = {'input': append_accessor(ddoc, dbin, sdoc['accessors'][s['input']], accessor_bytes(sdoc, sbin, s['input'])),
              'output': append_accessor(ddoc, dbin, sdoc['accessors'][s['output']], accessor_bytes(sdoc, sbin, s['output'])),
              'interpolation': s.get('interpolation', 'LINEAR')}
        out['samplers'].append(ns)
        out['channels'].append({'sampler': len(out['samplers']) - 1, 'target': {'node': dn[node], 'path': ch['target']['path']}})
    ddoc['animations'].append(out)


inst, new, out_inst, out_new = (Path(x) for x in sys.argv[1:5])
idoc, ibin = read_glb(inst); ibin = bytearray(ibin); ndoc, nbin = read_glb(new); nbin = bytearray(nbin)
i2 = copy.deepcopy(idoc); i2bin = bytearray(ibin)
for a in i2['animations']:
    if a['name'] == 'Attack':
        a['name'] = 'Attack2H'
i2['animations'] = [a for a in i2['animations'] if a['name'] not in ('Cast', 'AttackOneHand')]
copy_clip(ndoc, nbin, 'Attack', i2, i2bin, 'Attack'); copy_clip(ndoc, nbin, 'Cast', i2, i2bin, 'Cast')
write_glb(out_inst, i2, bytes(i2bin))
copy_clip(idoc, ibin, 'Attack', ndoc, nbin, 'Attack2H')
write_glb(out_new, ndoc, bytes(nbin))
print('VIEWER_CLIPS', out_inst.name, [a['name'] for a in i2['animations']], out_new.name, [a['name'] for a in ndoc['animations']])
