#!/usr/bin/env python3
"""Writes XD-12's project folders. `emit.py L3` writes devdocs/xeen/briefs/xd12/L3 (plan, rooms, project, diagram);
`emit.py L4` also the objects and wiring (dress.py). L1 and L2 are written by plan.py."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import copy
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shell  # noqa: E402,F401
import geo  # noqa: E402

R = Path(_REPO_ROOT)
BR = R / 'devdocs/xeen/briefs/xd12'


class D(yaml.SafeDumper):
    pass


def _flow_list(dumper, data):
    flow = all(not isinstance(x, (dict, list)) for x in data) or all(
        isinstance(x, list) and all(not isinstance(y, (dict, list)) for y in x) for x in data)
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=flow)


D.add_representer(list, _flow_list)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, Dumper=D, sort_keys=False, allow_unicode=True, width=120)


def rooms_doc(extra_rooms=None):
    rooms = []
    for rid in geo.ORDER:
        r = copy.deepcopy(geo.ROOMS[rid])
        if extra_rooms and rid in extra_rooms:
            extra_rooms[rid](r)
        rooms.append(r)
    return {'format': 0, 'themes': geo.THEMES, 'defaults': {'theme': 'theme:gate', 'ambient': 16}, 'rooms': rooms,
            'openings': geo.OPENINGS,
            'notes': "XD-12 Darzog's Tower: a square keep 6,144 across round a central well open to the sky; four floors 768 apart (gate 0, works 768, library 1536, Darzog's 2304) and a battlemented roof at 3072; two-storey stair halls alternate west and east; the island and Lake Darzog round the keep under the open sky. Written by output/studio_cal/xd12/tools/emit.py."}


if __name__ == '__main__':
    import plan
    level = sys.argv[1]
    folder = BR / level
    if level == 'L3':
        dump(folder / 'rooms.yml', rooms_doc())
        plan.write(level, folder)
    elif level == 'L4':
        import dress
        dress.write(folder)
        plan.write(level, folder)
    else:
        plan.write(level, folder)
