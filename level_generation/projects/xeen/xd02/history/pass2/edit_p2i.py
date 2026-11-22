#!/usr/bin/env python3
"""XD-02 second pass, step 9: the brake's key at the top of its condition (the build now refuses `consume` inside
`all`; the else branch tells freed from locked by the qbit), the flooded vein beside the hump's opening. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
O = yio.load(L + 'objects.yml')
W = yio.load(L + 'wiring.yml')
e = next(e for e in W['events'] if e['id'] == 'evt:brake')
e['condition'] = {'item': 'brake_key', 'consume': True}
v = next(o for o in O['switches'] if o['id'] == 'switch:vein_flooded')
v.update({'along': 0.104, 'size': [160, 128]})
next(o for o in O['lights'] if o['id'] == 'light:glint_flooded')['at'] = [12620, 1104]
yio.save(L + 'objects.yml', O)
yio.save(L + 'wiring.yml', W)
print('edited')
