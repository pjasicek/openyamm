import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# XD-02 dressing pass, after the pictures: the mess hall's heap off the west doorway (330, as a container would be);
# the adit mouth's heap away from the Red Dwarf Smithy's door (a wall panel the checker does not see as a door).
import sys; sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/a7')
from movelib import apply_dressing
apply_dressing(_REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4',
               {'deco:mess_hall_66': (7249, 7196), 'deco:adit_mouth_4': (13730, 2880)})
print('ok')
