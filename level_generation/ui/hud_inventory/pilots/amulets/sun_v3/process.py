"""Assess skull, sun, turquoise and Gothic amulets; retain native placement and matte evidence."""
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[2]
sys.path.insert(0, str(HUD))
import matte
import registration
from freeze_targets import rendered
from finalize_classification import ROOT, digest, read

spec = importlib.util.spec_from_file_location('cape_fitting', HUD / 'pilots/boots/process.py')
fitting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fitting)
attempt = next(a for a in read('checkpoint/state.json')['attempts']
               if a['id'] == 'd23f246533fe4ee4b218f8372f5523d1')
assert digest(Path(attempt['raw'])) == attempt['sha256']
job = next(j for j in read('jobs.json')['jobs'] if j['id'] == attempt['job'])
targets = {t['id']: t for t in read('expected_targets.json')['targets']}
raw = Image.open(attempt['raw']).convert('RGB')
sx, sy = raw.width / job['reference_size'][0], raw.height / job['reference_size'][1]
crops = [(round(x*sx), round(y*sy), round((x+w)*sx), round((y+h)*sy))
         for x,y,w,h in (m['reference_cell_rect'] for m in job['members'])]
sheet = Image.open(OUT.parent / 'batch2/gothic_final/complete-sheet.png').convert('RGB')
draw = ImageDraw.Draw(sheet)
records = []
for i, (member, crop) in enumerate(zip(job['members'][1:3], crops[1:3]), start=1):
    target = targets[member['target']]
    name = target['runtime_name']
    clean, stats = matte.extract(raw.crop(crop))
    clean.save(OUT / f'{name}-clean-master.png')
    with Image.open(ROOT / member['source_path']) as source:
        native = rendered(source, 'item').resize(tuple(member['export_region'][2:]), Image.Resampling.NEAREST)
    transform, iou = fitting.fit(clean, native)
    candidate = fitting.transform(clean.convert('RGBa'), native.size, transform).convert('RGBA')
    artifact = OUT / f'{name}.png'
    candidate.save(artifact)
    review = registration.evidence(member, target, artifact, OUT / 'registration')
    edge = Image.new('RGB', (native.width * 2, native.height + 24))
    for j, bg in enumerate(('#eeeeee', '#171717')):
        tile = Image.new('RGBA', candidate.size, bg)
        tile.alpha_composite(candidate)
        edge.paste(tile.convert('RGB'), (j * native.width, 24))
    edge.save(OUT / f'{name}-light-dark.png')
    tile = Image.new('RGBA', candidate.size, '#292929')
    tile.alpha_composite(candidate)
    x, y = (i % 3) * 100, (i // 3) * 200
    draw.text((x + 8, y + 4), name, fill='white')
    sheet.paste(tile.convert('RGB'), (x + 8, y + 24))
    records.append(dict(cell=member['id'], artifact=str(artifact), raw_crop_xyxy=crop,
                        uniform_scale_translate_xy=transform, diagnostic_silhouette_iou=iou,
                        cleanup=stats, **review))
sheet.save(OUT / 'complete-sheet.png')
(OUT / 'processing.json').write_text(json.dumps(dict(attempt=attempt['id'], raw_sha256=attempt['sha256'],
    script_sha256=digest(Path(__file__)), matte_sha256=digest(Path(matte.__file__)),
    fitting_sha256=digest(Path(fitting.__file__)), cells=records), indent=2) + '\n')
print(json.dumps([{k: r[k] for k in ('cell', 'failures')} for r in records], indent=2))
