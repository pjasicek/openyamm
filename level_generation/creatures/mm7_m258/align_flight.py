"""Apply reviewed native beak landmarks as whole-frame integer translations."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
landmarks = json.loads((P/'flight_alignment.json').read_text())['frames']
registration = json.loads((P/'registration.json').read_text())
backup = P/'checkpoints/before_flight_alignment'
backup.mkdir(parents=True, exist_ok=True)
for name, record in landmarks.items():
    path = P/f'aligned_2x/{name}.png'
    if registration[name].get('flight_landmark_translation_px'):
        continue
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['aligned_before_sha256'], name
    before = Image.open(path)
    if not (backup/path.name).exists():
        (backup/path.name).write_bytes(path.read_bytes())
    dx, dy = record['proposed_translation']
    left, top = min(0, dx), min(0, dy)
    after = Image.new('RGBA', (before.width+abs(dx), before.height+abs(dy)))
    after.paste(before, (dx-left, dy-top))
    recovered = after.crop((dx-left, dy-top, dx-left+before.width, dy-top+before.height))
    assert np.array_equal(np.array(before), np.array(recovered))
    after.save(path)
    reg = registration[name]
    reg['canvas_origin_px'] = [reg['canvas_origin_px'][0]+left, reg['canvas_origin_px'][1]+top]
    reg['translate'] = [reg['translate'][0]+dx, reg['translate'][1]+dy]
    reg['flight_landmark_translation_px'] = [dx, dy]
    reg['method'] += ' Reviewed native beak translation baked into pixels; no resampling.'
(P/'registration.json').write_text(json.dumps(registration, indent=2)+'\n')
print('Applied reviewed flight translations; run variants.py next to rebuild matching masks.')
