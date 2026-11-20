import json
import sys
from pathlib import Path
from PIL import Image
p = Path(__file__).resolve().parent
root = p.parents[2]
sys.path.insert(0, str(root))
from finish import clean_solid, register_cell, check_existing
job = json.loads((root / 'jobs/g08111_v0_s0.json').read_text())
sources = json.loads((root / 'sources.json').read_text())
raw = Image.open(p / 'raw.png')
# Reviewed autumn foliage is red/orange on magenta; inspect direct chroma extraction against the eroded old mask.
clean, stats = clean_solid(raw, [255, 0, 255])
cell = job['cells'][0]
cell['native_bounds'] = sources[cell['asset']]['native_bounds']
clean.save(p / (cell['asset'] + '.master.png'))
output, registration = register_cell(clean, job, cell, raw.size)
output.save(p / (cell['asset'] + '.png'))
(p / 'extraction_correction.json').write_text(json.dumps({'cleanup': stats, 'registration': registration, 'reason': 'Old mask erodes foliage; direct magenta extraction is a candidate requiring visual review.'}, indent=2) + '\n')
check_existing(job, sources, p)
