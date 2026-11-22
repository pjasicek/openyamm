#!/usr/bin/env python3
"""XD-02 second pass, step 5: the standing carts' flared tubs at sizes and a turn whose corners fall on whole units
(180 by 100 flaring to 200 by 120; the stope's cart turned 36.87 degrees, a 3-4-5 turn), since a flared block at 30
degrees has corners off the grid and faces that are not flat. Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import math, sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
ANG = math.degrees(math.atan2(3, 4))
for r in R['rooms']:
    for p in r.get('platforms', []):
        if p.get('top_size') == [200, 128]:
            p['size'] = [180, 100]
            p['top_size'] = [200, 120]
        if r['id'] == 'room:stope_floor' and p.get('facing') == 30:
            p['facing'] = round(ANG, 4)
            if 'at' in p and p['at'] != [6050, 3400]:
                # re-place the wheel about the cart's middle at the new turn
                dx, dy = p['at'][0] - 6050, p['at'][1] - 3400
                a = math.radians(30)
                along = dx * math.cos(a) + dy * math.sin(a)
                across = -dx * math.sin(a) + dy * math.cos(a)
                b = math.radians(ANG)
                p['at'] = [round(6050 + math.cos(b) * along - math.sin(b) * across, 1),
                           round(3400 + math.sin(b) * along + math.cos(b) * across, 1)]
yio.save(L + 'rooms.yml', R)
print('edited', ANG)
