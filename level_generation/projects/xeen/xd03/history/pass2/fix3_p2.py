#!/usr/bin/env python3
"""Pass two, fix 3: end faces whose pictures were stretched (the build has no word to say it is meant)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
rooms = yio.load(L + 'rooms.yml')
R = {r['id']: r for r in rooms['rooms']}
for p in R['room:furnace_hall']['platforms']:
    if p.get('id') == 'platform:furnace_mouth':
        # 72 deep, so its ends (72 x 144) take the granite at its shape.
        p['at'] = [4224, 2404]
        p['size'] = [176, 72]
        p['end_surface'] = {'texture': 'vlcwl3a', 'size': [128, 256]}
    if p.get('notes') == "The mouth's iron lintel":
        p['at'] = [4224, 2432]
    if str(p.get('id', '')).startswith('platform:gong_'):
        p['end_surface'] = {'texture': 'bemvwal', 'size': [128, 256]}   # the rim, 12 x 24
        p['top_surface'] = {'texture': 'vlcgnrc1', 'size': [256, 256]}
for p in R['room:king_hall']['platforms']:
    if str(p.get('notes', '')).startswith("The throne's crest"):
        p['end_surface'] = {'texture': 'trim11_16', 'size': [16, 64]}   # its 40 x 192 edges, dark trim
yio.save(L + 'rooms.yml', rooms)
