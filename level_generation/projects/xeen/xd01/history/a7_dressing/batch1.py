import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-01 dressing pass (DRESSING.md, 2026-11-20): sacks off the doorways, the grain hall's clumps made pairs.
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd01/L4', {
    'deco:feed_sacks_1': (492, 4913), 'deco:feed_sacks_2': (584, 5000), 'deco:feed_sacks_3': (741, 5035),
    'deco:feed_sacks_5': (930, 5043), 'deco:bay_sacks_1': (1180, 1018), 'deco:bay_sacks_2': (1367, 1159),
    'deco:hall_sacks_4': (433, 1831), 'deco:hall_sacks_3': (1460, 1920)},
    removes=('deco:feed_sacks_6', 'deco:hall_barrel_1', 'deco:hall_sacks_5', 'deco:aisle_sacks_3'))
print('ok')
