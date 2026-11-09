"""Record measured complete-sheet alpha borders without granting visual acceptance."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path.cwd()
SESSION = ROOT / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'
for family in sorted(SESSION.glob('mm7_m*')):
    run = json.loads((family / 'redo_2x/run.json').read_text())
    records = {}
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        path = ROOT / job['selected_raw']
        alpha = np.array(Image.open(path).convert('RGBA'))[:, :, 3]
        counts = {side: int((values >= 64).sum()) for side, values in
            [('left', alpha[:, :3]), ('right', alpha[:, -3:]), ('top', alpha[:3]), ('bottom', alpha[-3:])]}
        records[job['id']] = dict(raw=job['selected_raw'], solid_outer_border_pixels=counts,
            potential_clipping=any(counts.values()), reviewed=False)
    (family / 'redo_2x/review/raw_border_audit.json').write_text(json.dumps(records, indent=2) + '\n')
    print(family.name, {job: r['solid_outer_border_pixels'] for job, r in records.items() if r['potential_clipping']})
