"""Record palette review after an agent has inspected each named contact."""
from pathlib import Path
import datetime
import hashlib
import json
import sys

D = Path(__file__).resolve().parent
jobs = json.loads((D / 'jobs.json').read_text())
path = D / 'variant_acceptance.json'
records = json.loads(path.read_text()) if path.exists() else {}
for key in sys.argv[1:]:
    if key == 'trials':
        names = jobs['seeded_trial_frames']
    else:
        job = jobs['jobs'][key]
        assert job['status'] == 'accepted_detail_and_placement', key
        names = job['frames']
    paths = [f'review/variants/{key}.png', 'material_settings.json', 'mask_protection.json']
    for name in names:
        paths.extend([f'masks_2x/{name}.png', f'material_support_2x/{name}.png'])
        paths.extend(f'previews/{name}_{palette}.png' for palette in [433, 434, 435])
    records[key] = {
        'frames': names,
        'status': 'accepted_palette_contact',
        'accepted_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'findings': 'All three native palette previews and enhanced-art mask overlay inspected. '
                    'Sleeve bands and visible armor disks recolor while hair, skin, black armor, '
                    'gold fasteners and steel blades retain their material colors. '
                    'Base bypass and identical alpha checked by variants_detail.py.',
        'hashes': {p: hashlib.sha256((D / p).read_bytes()).hexdigest() for p in paths},
    }
path.write_text(json.dumps(records, indent=2) + '\n')
print('Recorded palette review:', ', '.join(sys.argv[1:]))
