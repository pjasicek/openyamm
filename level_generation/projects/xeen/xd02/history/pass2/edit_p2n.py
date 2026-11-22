#!/usr/bin/env python3
"""XD-02 second pass, step 14: the west line's derailed cart stands square against the south wall (askew it closed
the tunnel to `oymap solve`, though the playtest's walker squeezed past). Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
r = next(r for r in R['rooms'] if r['id'] == 'room:west_line')
for p in r['platforms']:
    if 'facing' in p and abs(p['facing'] - 36.8699) < 0.01:
        a = math.radians(p['facing'])
        dx, dy = p['at'][0] - 6200, p['at'][1] - 5184
        along = dx * math.cos(a) + dy * math.sin(a)
        across = -dx * math.sin(a) + dy * math.cos(a)
        p['at'] = [round(6200 + along, 1), round(5104 + across, 1)]
        p['facing'] = 0
    if p.get('notes', '').startswith('The derailed cart'):
        p['notes'] = 'The derailed cart, shoved off the line against the south wall.'
yio.save(L + 'rooms.yml', R)
print('edited')
