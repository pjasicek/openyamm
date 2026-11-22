#!/usr/bin/env python3
"""XD-27: L3 plan/project from L2 (+ sketch), and L4's plan (the L3 plan) and diagram. Rooms come from gen.py --l3."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path
import yaml
R = Path(_REPO_ROOT)
B = R / 'devdocs/xeen/briefs/xd27'
plan = yaml.safe_load((B / 'L2/plan.yml').read_text())
proj = yaml.safe_load((B / 'L2/project.yml').read_text())
plan['level'] = 'L3'
plan['sketch'] = {'file': 'rooms.yml', 'grid': 512}
extra = (" L3: drawn to scale as thirteen rooms, one per space (output/studio_cal/xd27/tools/gen.py --l3); the throwing "
         "ledge faces east over the gorge (X2 puts the lair in the bluff west of the north river, so the river lies east "
         "of the lair), the boulder slide leaves the ledge's south end into the rock; the Chieftain's den is one step "
         "(32) above the feast cave, not 64; the bone den's way down is a rock terrace and six steps inside the feast "
         "cave; the cooking pit is a hollow with sloping sides (bank) rather than two steps. Footprint 17 x 15 cells.")
if 'L3:' not in plan['notes']:
    plan['notes'] += extra
proj['notes'] = proj['notes'].replace('level L2', 'level L3')
proj['extent'] = {'footprint_cells': [17, 15], 'climbs': 'n'}
for lv in ('L3', 'L4'):
    (B / lv).mkdir(parents=True, exist_ok=True)
    (B / lv / 'plan.yml').write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=120))
    (B / lv / 'diagram.txt').write_text((B / 'L2/diagram.txt').read_text())
(B / 'L3/project.yml').write_text(yaml.safe_dump(proj, sort_keys=False, allow_unicode=True, width=120))
print('L3 plan/project, L4 plan written')
