import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-04 dressing pass (DRESSING.md, 2026-11-20): props off the doorways and walking lines, containers to the walls.
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd04/L4', {
    'deco:altar_pot': (-3330, 560), 'deco:broken_balcony_bones': (-1277, 1471), 'deco:cask_1': (-458, -540),
    'deco:dorm_bucket': (2985, 904), 'deco:hoist_sacks': (-2355, -689), 'deco:vat_hall_cask': (-612, 3046),
    'deco:vat_hall_pot': (-553, 2006), 'deco:vat_hall_sacks': (-1615, 1709)},
    removes=('deco:gallery_cask', 'deco:gallery_cask_2', 'deco:loft_sacks', 'deco:loft_sacks_2'))
print('ok')
