#!/usr/bin/env python3
"""Pass two, fix 1: after the first validate (hinged leaves cannot tile; `sources` only on step events; a niche short)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys, copy
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
rooms = yio.load(L + 'rooms.yml'); objects = yio.load(L + 'objects.yml'); wiring = yio.load(L + 'wiring.yml')
r = next(r for r in rooms['rooms'] if r['id'] == 'room:sentry_lookout')
r['outline'] = [[6528, 2432], [6848, 2432], [6848, 2816], [6528, 2816]]
for d in objects['doors']:
    if d['id'] in ('door:armoury', 'door:sentry', 'door:tower'):
        # Two plank halves 128 x 256 that fold sideways to the jambs, the planks at their size.
        d.pop('hinge', None)
        d.update({'kind': 'slide_left', 'leaves': 2, 'fold': True, 'tile': True})
    if d['id'] in ('door:barracks_e', 'door:barracks_w'):
        # The Forge's own slab door (cvdor1, 128 x 256), the two leaves side by side.
        d.pop('tile', None)
        d['surface'] = {'texture': 'cvdor1', 'size': [128, 256], 'fit': True}
for d in objects['decorations']:
    if d['id'] == 'deco:warren_rock_2':
        d['at'] = [3200, 620]
g = next(e for e in wiring['events'] if e['id'] == 'evt:gong')
g.pop('sources', None)
for k in range(2, 9):
    c = copy.deepcopy(g)
    c['id'] = f'evt:gong_{k}'
    c['source'] = f'platform:gong_{k}'
    c['notes'] = 'The same as evt:gong, for another slab of the gong (a clicked event has one source).'
    wiring['events'].append(c)
yio.save(L + 'rooms.yml', rooms); yio.save(L + 'objects.yml', objects); yio.save(L + 'wiring.yml', wiring)
