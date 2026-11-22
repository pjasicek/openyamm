import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-02 dressing pass (DRESSING.md, 2026-11-20): props off the doorways and walking lines, containers to the walls.
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4', {
    'deco:adit_mouth_2': (13402, 3916), 'deco:adit_mouth_3': (13756, 3942), 'deco:deep_station_100': (4322, 4725),
    'deco:lamp_room_26': (11868, 4518), 'deco:mess_hall_66': (7141, 7225), 'deco:spider_galleries_104': (5000, 1054),
    'deco:stope_floor_91': (5716, 2628), 'deco:stope_floor_93': (5888, 3654), 'deco:top_station_15': (13286, 5220),
    'deco:top_station_19': (12262, 5032), 'deco:turntable_47': (7720, 5576), 'deco:turntable_48': (8045, 5932)},
    removes=('deco:top_station_17', 'deco:top_station_18'))
print('ok')
