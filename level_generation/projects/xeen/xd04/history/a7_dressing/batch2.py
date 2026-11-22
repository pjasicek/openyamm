import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-04: the vat hall's pot out of the way of the loft steps' doorway (A3's playthrough stuck there, 2026-11-20).
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd04/L4', {'deco:vat_hall_pot': (-800, 2072)})
print('ok')
