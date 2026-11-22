import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-02 dressing pass, second step: the Turntable's other barrel beside the first (a pair a stride apart).
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4', {'deco:turntable_46': (7869, 5765)})
print('ok')
