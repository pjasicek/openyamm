import json
import sys
from pathlib import Path
from PIL import Image
p = Path(__file__).resolve().parent
root = p.parents[2]
sys.path.insert(0, str(root))
from finish import clean_solid, register_cell, check_existing
job = json.loads((root / 'jobs/g17675_v0_s0.json').read_text())
sources = json.loads((root / 'sources.json').read_text())
raw = Image.open(p / 'raw.png')
# Reviewed gray metal contains no magenta; key the actual generated backdrop.
clean, stats = clean_solid(raw, [255, 0, 255])
cell = job['cells'][0]
cell['native_bounds'] = sources[cell['asset']]['native_bounds']
clean.save(p / (cell['asset'] + '.master.png'))
output, registration = register_cell(clean, job, cell, raw.size, adjust=(1.0, 0.0, 42.0))
output.save(p / (cell['asset'] + '.png'))
(p / 'extraction_correction.json').write_text(json.dumps({'cleanup': stats, 'registration': registration, 'reason': 'Reviewed gray metal plate has no magenta material; use actual generated magenta backdrop.'}, indent=2) + '\n')
check_existing(job, sources, p)
