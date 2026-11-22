#!/usr/bin/env python3
"""XD-02 second pass, step 6: the spiral's ledge torches at heights above the room's floor that put them on their
ledges (a wall decoration's floor_height is not honoured: they stood inside the benches); the trestle's X braces in
the post timber (their raked ends squashed the beam picture). Run once."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
O = yio.load(L + 'objects.yml')
ledge_top = {84: -544, 85: -704, 86: -864, 87: -1024, 88: -384}
for d in O['decorations']:
    for n, top in ledge_top.items():
        if d['id'] == f'deco:stope_floor_{n}':
            d['height'] = top + 200 - (-1152)
for r in R['rooms']:
    if r['id'] == 'room:chasm':
        for b in r['beams']:
            if 'bottom_end' in b and b['width'] == 16:
                b['surface'] = {'texture': 't3d2abs', 'size': [32, 256]}
yio.save(L + 'rooms.yml', R)
yio.save(L + 'objects.yml', O)
print('edited')
