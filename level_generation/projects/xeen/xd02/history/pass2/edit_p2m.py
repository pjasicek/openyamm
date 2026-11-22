#!/usr/bin/env python3
"""XD-02 second pass, step 13: every cart carries ore (an empty iron tub read as an iron box) and its wheels stand
just outside the flaring rim, 48 across, where the eye sees them. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
ORE = {'texture': 'crdrf1', 'size': [128, 128]}
for r in R['rooms']:
    plats = r.get('platforms', [])
    tubs = [p for p in plats if p.get('top_size') == [200, 120]]
    for tub in tubs:
        tub['top_surface'] = ORE
        cx, cy = tub['at']
        a = math.radians(tub.get('facing', 0))
        for p in plats:
            if p.get('notes') == 'Cart wheel' and math.hypot(p['at'][0] - cx, p['at'][1] - cy) < 100:
                dx, dy = p['at'][0] - cx, p['at'][1] - cy
                along = dx * math.cos(a) + dy * math.sin(a)
                across = -dx * math.sin(a) + dy * math.cos(a)
                across = 66 if across > 0 else -66
                p['at'] = [round(cx + math.cos(a) * along - math.sin(a) * across, 1),
                           round(cy + math.sin(a) * along + math.cos(a) * across, 1)]
                p['size'] = [48, 10]
                p['rise'] = 48
    for p in plats:
        if p.get('notes', '').startswith('An abandoned ore cart, empty'):
            p['notes'] = 'An abandoned ore cart, half full.'
yio.save(L + 'rooms.yml', R)
print('edited')
