#!/usr/bin/env python3
"""XD-02 second pass, step 11: the brake wheel on a pedestal that holds it, the capstan's bars at two levels (they
crossed in one plane), the skeleton clear of a spider. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml'); O = yio.load(L + 'objects.yml')
for r in R['rooms']:
    for p in r.get('platforms', []):
        if p.get('notes') == "The brake's post":
            p['size'] = [48, 48]
            p['notes'] = "The brake's iron-capped post"
        if p.get('id') == 'platform:brake_wheel':
            p['outline'] = [[round(4239 + 32 * math.cos(math.radians(22.5 + 45 * k))),
                             round(4856 + 32 * math.sin(math.radians(22.5 + 45 * k)))] for k in range(8)]
    for b in r.get('beams', []):
        if b.get('notes') == 'Capstan bar':
            b['bottom'] = 340 if b['path'][0][1] == 5300 else 352
for d in O['decorations']:
    if d['id'] == 'deco:spider_galleries_102':
        d['at'] = [3440, 1340]
yio.save(L + 'rooms.yml', R); yio.save(L + 'objects.yml', O)
print('edited')
