"""Lane A5 (2026-11-21): AU's outdoor beds (devdocs/xeen/AUDIO.md "Outdoor beds", copied into <map>.yml here) merged
into a map's L3/L4 sketch `sounds` by its generator's dump(); a sound the generator writes itself (X6's sand-falls)
keeps its own entry (same id wins)."""
import os

import yaml

HERE = os.path.dirname(os.path.realpath(__file__))


def with_beds(data, key):
    if not isinstance(data, dict) or 'structures' not in data:
        return data
    beds = yaml.safe_load(open(os.path.join(HERE, key + '.yml')))['sounds']
    own = list(data.get('sounds') or [])
    ids = {s['id'] for s in own}
    data = dict(data)
    data['sounds'] = [b for b in beds if b['id'] not in ids] + own
    return data
