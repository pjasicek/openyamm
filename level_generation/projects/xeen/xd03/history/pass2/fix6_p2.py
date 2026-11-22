#!/usr/bin/env python3
"""Pass two, fix 6: after the pictures of every thing: torches that hung in doorways, the statues' line."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
objects = yio.load(L + 'objects.yml'); wiring = yio.load(L + 'wiring.yml')
D = {d['id']: d for d in objects['decorations']}
D['deco:barracks_torch_2']['along'] = 0.254   # was in the armoury doorway
D['deco:armoury_torch']['along'] = 0.15       # was in the armoury doorway (its other side)
D['deco:gallery_torch_1']['along'] = 0.40     # was in the sentry doorway
for e in wiring['events']:
    if e['id'] in ('evt:statue_e', 'evt:statue_w'):
        e['text'] = ("A Red Dwarf king carved in stone, older than the clan. Fresh axe marks scar his plinth: the Mad"
                     " Dwarves have no love for the old kings.")
yio.save(L + 'objects.yml', objects); yio.save(L + 'wiring.yml', wiring)
