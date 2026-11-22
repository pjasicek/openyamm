#!/usr/bin/env python3
"""XD-02 second pass, step 7: the hoist's head frame: the cross-head that spanned the two arms in the air becomes the
sheave beam, run out of the rock between the arms to over the cable (it touches the wall it comes out of); the X
braces back in the beam timber (their squashed ends are inside the legs and unseen). Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
for r in R['rooms']:
    if r['id'] == 'room:chasm':
        for b in r['beams']:
            if 'bottom_end' in b and b['width'] == 16:
                b['surface'] = {'texture': 't3d2abe', 'size': [256, 32]}
    if r['id'] == 'room:stope_floor':
        for b in r['beams']:
            if b.get('notes') == "Head frame cross-head with the sheave's axle":
                b['path'] = [[7000, 3670], [6890, 3560]]
                b['notes'] = "Head frame: the sheave beam out of the rock between the arms, the cable hanging from its end"
yio.save(L + 'rooms.yml', R)
print('edited')
