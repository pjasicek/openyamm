import json
import sys
from pathlib import Path
from PIL import Image
p = Path(__file__).resolve().parent
root = p.parents[2]
sys.path.insert(0, str(root))
from finish import clean_solid, register_cell, check_existing
job = json.loads((root / 'jobs/g08059_v0_s0.json').read_text())
sources = json.loads((root / 'sources.json').read_text())
raw = Image.open(p / 'raw.png')
# This reviewed raw is one solid gray rock on cyan; the cyan reference
# collision statistic is not evidence of cyan material in this generated master.
clean, stats = clean_solid(raw, job['matte_rgb'])
cell = job['cells'][0]
cell['native_bounds'] = sources[cell['asset']]['native_bounds']
clean.save(p / (cell['asset'] + '.master.png'))
output, registration = register_cell(clean, job, cell, raw.size)
output.save(p / (cell['asset'] + '.png'))
(p / 'extraction_correction.json').write_text(json.dumps({'cleanup': stats, 'registration': registration, 'reason': 'Old mask visibly shrank rock and produced red outline; reviewed solid-gray master has no cyan material.'}, indent=2) + '\n')
check_existing(job, sources, p)
