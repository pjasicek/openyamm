#!/usr/bin/env python3
"""Drop animation channels whose target node name starts with one of the prefixes (default the retired skirt cage
Skirt_* and its HemOpening marker, keyed per clip to follow the old cage hem; the gate's cloth containment uses the
marker's opening plane, which must now ride with the pelvis like the re-skinned skirt).
Usage: strip_channels.py <in.glb> <out.glb> [prefix ...]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, out = Path(sys.argv[1]), Path(sys.argv[2]); prefixes = tuple(sys.argv[3:] or ['Skirt_', 'HemOpening'])
doc, binary = read_glb(src); names = [n.get('name', '') for n in doc['nodes']]; dropped = 0
for anim in doc['animations']:
    keep = [c for c in anim['channels'] if not names[c['target']['node']].startswith(prefixes)]
    dropped += len(anim['channels']) - len(keep)
    used = sorted({c['sampler'] for c in keep}); smap = {o: n for n, o in enumerate(used)}
    anim['samplers'] = [anim['samplers'][i] for i in used]
    for c in keep:
        c['sampler'] = smap[c['sampler']]
    anim['channels'] = keep
write_glb(out, doc, binary)
print('STRIPPED', dropped, 'channels')
