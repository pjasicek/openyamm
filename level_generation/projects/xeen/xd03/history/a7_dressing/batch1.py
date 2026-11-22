import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-03 dressing pass (DRESSING.md, 2026-11-20): props off the doorways and walking lines, containers to the walls.
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4', {
    'deco:armoury_barrel': (5824, 4260), 'deco:armoury_cask': (5824, 4700), 'deco:bowl_1': (4640, 4352),
    'deco:breach_rock': (2308, 1600), 'deco:flambeau_far_1': (2705, 2896), 'deco:flambeau_far_2': (3484, 3728),
    'deco:flambeau_near_2': (4393, 3075), 'deco:geode_glow_2': (1089, 1564), 'deco:lower_glow': (364, 389),
    'deco:stalagmite_1': (1057, 1143), 'deco:hoard_thief': (3452, 6705), 'deco:hoard_thief_bones': (3398, 6632),
    'deco:spoil_2': (4207, 1634)},
    removes=('deco:barracks_barrel_1',))
print('ok')
