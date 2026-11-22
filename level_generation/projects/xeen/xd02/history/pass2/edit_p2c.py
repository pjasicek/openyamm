#!/usr/bin/env python3
"""XD-02 second pass, step 3 (after edit_p2b.py): the chapel's tablet becomes a bronze plaque set in the south wall
over a stone ledge (the schema refuses `uneven` on a surface that the build's own squash warning recommends); the
plinth and step as outlines laid at size. Run once; not to be run again."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys

sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd02/pass2')
import yio

L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4/'
R = yio.load(L + 'rooms.yml')
W = yio.load(L + 'wiring.yml')

c = next(r for r in R['rooms'] if r['id'] == 'room:dwarf_shrine')
STONE = {'texture': 'd7trim8', 'size': [64, 64]}
keep = [p for p in c['platforms'] if p.get('id') == 'platform:green_pool']
c['platforms'] = keep + [
    {'rise': 112, 'surface': STONE, 'top_surface': STONE,
     'outline': [[8416, 2180], [8736, 2180], [8736, 2228], [8416, 2228]],
     'notes': "The tablet's ledge of dressed stone against the south wall"},
    {'rise': 16, 'surface': STONE, 'top_surface': {'texture': 'd7flor4', 'size': [128, 128]},
     'outline': [[8400, 2228], [8752, 2228], [8752, 2300], [8400, 2300]], 'notes': "The step before the tablet"},
]
c['walls'] = [{'wall': 6, 'panels': [
    {'id': 'panel:chapel_tablet', 'at': 'centre', 'length': 256, 'bottom': 144, 'height': 128,
     'surface': {'texture': 'sign128', 'size': [256, 128], 'fit': True},
     'notes': "The Red Dwarves' tablet: a bronze plaque of runes set in the south wall over its ledge, facing the door."}]}]
e = next(e for e in W['events'] if e['id'] == 'evt:tablet')
e['source'] = 'panel:chapel_tablet'

yio.save(L + 'rooms.yml', R)
yio.save(L + 'wiring.yml', W)
print('edited')
