#!/usr/bin/env python3
"""Pass two, fix 2: after the first build's warnings."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
rooms = yio.load(L + 'rooms.yml'); objects = yio.load(L + 'objects.yml')
R = {r['id']: r for r in rooms['rooms']}
# Trestle posts as wide as the caps' quarter points (the caps rest on them), ending at the caps' foot.
for p in R['room:deep_landing']['platforms']:
    if p.get('notes') == 'Trestle post':
        p['size'] = [24, 24]
# The cut's last timber set: the cap runs wall to wall.
for b in R['room:sentry_cut']['beams']:
    if b['path'][0][0] == 5600:
        b['path'] = [[5600, 2592], [5600, 2912]]
# Narrow end faces that cannot show a whole picture: stretched on purpose.
for p in R['room:furnace_hall']['platforms']:
    if p.get('id') == 'platform:furnace_mouth':
        p['end_surface'] = {'texture': 'vlcwl3a', 'size': [128, 256], 'uneven': True}
    if str(p.get('id', '')).startswith('platform:gong_'):
        p['end_surface'] = {'texture': 'vlcgnrc1', 'size': [256, 256], 'uneven': True}
        p['top_surface'] = {'texture': 'vlcgnrc1', 'size': [256, 256], 'uneven': True}
for p in R['room:king_hall']['platforms']:
    if str(p.get('notes', '')).startswith("The throne's crest"):
        p['end_surface'] = {'texture': 'vlcwl3a', 'size': [128, 256], 'uneven': True}
for p in R['room:kings_antechamber']['platforms']:
    p['rise'] = 480   # the lifted upper bar's top met the brackets' tops in one plane at 448
# Wall decorations take their height from the room's floor (floor_height is not read for them: tool defect).
for d in objects['decorations']:
    if d['id'] in ('deco:gallery_torch_1', 'deco:gallery_torch_2'):
        d['height'] = 384 + 176
    if d['id'] == 'deco:shaft_lamp':
        d['height'] = 1536 + 176
yio.save(L + 'rooms.yml', rooms); yio.save(L + 'objects.yml', objects)
