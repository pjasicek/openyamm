#!/usr/bin/env python3
"""Restore the Knife node and the right-hand fist's local transform in Attack from the pre-audit attack (2026-11-12, coordinator).

The donor_attack.py pass-through bug (fixed 2026-11-11 for m416) wrote the Knife's Standing frame-0 transform into the
re-animated Attack: scale 0.001 (the parked, hidden knife), so she stabbed empty-handed. The knife is a child of the
hand, so its original Attack transform (the grip) applies unchanged to the new arm motion.
    restore_knife.py <installed.glb> <pre-audit.glb> <out.glb>
"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
import glb_pose  # noqa: E402

after, before, out = sys.argv[1:4]
g, b = glb_pose.Glb(after), glb_pose.Glb(before)
def attack_channels(glb):
    names = [n.get('name', '') for n in glb.json['nodes']]
    anim = next(a for a in glb.json['animations'] if a['name'] == 'Attack')
    return anim, {(names[c['target']['node']], c['target']['path']): c for c in anim['channels']}
anim_a, ch_a = attack_channels(g)
anim_b, ch_b = attack_channels(b)
# The knife's grip transform, and the right hand's fist (the donor clip held the fingers open: the knife floated).
targets = [('Knife', path, kind) for path, kind in (('translation', 'VEC3'), ('rotation', 'VEC4'), ('scale', 'VEC3'))]
targets += [(node, 'rotation', 'VEC4') for node, path in ch_b if path == 'rotation' and node.startswith('B_R_Finger')]
for node, path, kind in targets:
    src = b.accessor(anim_b['samplers'][ch_b[(node, path)]['sampler']]['output'])
    sampler = anim_a['samplers'][ch_a[(node, path)]['sampler']]
    count = g.json['accessors'][sampler['input']]['count']
    value = src[0] if np.allclose(src, src[0], atol=1e-6) else None
    if value is None:
        raise SystemExit(f'{node} {path}: the original Attack animates it; resample instead of a constant')
    sampler['output'] = g.append_accessor(np.repeat(value[None], count, axis=0), kind)
    print(node, path, 'restored')
g.write(out)
