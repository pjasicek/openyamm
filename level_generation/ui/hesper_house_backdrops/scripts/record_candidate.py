"""Preserve a built-in imagegen return and its provenance in this backdrop batch."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

project = Path(__file__).resolve().parents[1]
manifest = project / 'generation_runs_house_backdrops.json'
data = json.loads(manifest.read_text())
job = data['jobs'][int(sys.argv[1])]
source = Path(sys.argv[2])
target = project / 'candidates' / f"{job['key']}_{job['candidate']}.png"
assert not target.exists(), target
shutil.copy2(source, target)
with Image.open(target) as image:
    job.update(status='generated', file=str(target.relative_to(project)), source_path=str(source),
               size=list(image.size), mode=image.mode, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
manifest.write_text(json.dumps(data, indent=2) + '\n')
print(target, job['size'])
