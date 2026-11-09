"""Extract the nine-item imagegen benchmark using existing matte and uniform fitting."""
import importlib.util
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[1]
sys.path.insert(0, str(HUD))
import matte
import registration
from freeze_targets import rendered
from finalize_classification import ROOT, digest, read

spec = importlib.util.spec_from_file_location('item_fitting', HUD / 'pilots/boots/process.py')
fitting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fitting)
started = time.monotonic()
manifest = json.loads((OUT / 'manifest.json').read_text())
targets = {t['id']: t for t in read('expected_targets.json')['targets']}
raw = Image.open(OUT / 'raw.png').convert('RGB')
sx, sy = raw.width / manifest['reference_size'][0], raw.height / manifest['reference_size'][1]
sheet = Image.new('RGB', (1400, 1320), '#454545')
draw = ImageDraw.Draw(sheet)
records = []
for i, row in enumerate(manifest['rows']):
    member = row['member']
    name = Path(member['source_path']).stem
    x, y, w, h = row['cell_rect']
    crop = (round(x*sx), round(y*sy), round((x+w)*sx), round((y+h)*sy))
    clean, stats = matte.extract(raw.crop(crop))
    clean.save(OUT / f'{name}-master.png')
    with Image.open(ROOT / member['source_path']) as source:
        native = rendered(source, 'item').resize(tuple(member['export_region'][2:]), Image.Resampling.NEAREST)
    values, iou = fitting.fit(clean, native)
    candidate = fitting.transform(clean.convert('RGBa'), native.size, values).convert('RGBA')
    artifact = OUT / f'{name}.png'
    candidate.save(artifact)
    review = registration.evidence(member, targets[member['target']], artifact, OUT / 'registration')
    px, py = (i % 2)*700, (i // 2)*660
    draw.text((px+6, py+6), f'{name}: original x2 | restored x2', fill='white')
    for offset, im in ((5, native), (355, candidate)):
        tile = Image.new('RGBA', im.size, '#454545')
        tile.alpha_composite(im)
        sheet.paste(tile.convert('RGB'), (px+offset, py+30))
    for offset, bg in ((5, '#eeeeee'), (355, '#111111')):
        thumb = Image.new('RGBA', candidate.size, bg)
        thumb.alpha_composite(candidate)
        thumb.thumbnail((150, 46))
        sheet.paste(thumb.convert('RGB'), (px+offset, py+760))
    records.append(dict(cell=member['id'], artifact=str(artifact), raw_crop_xyxy=crop,
                        uniform_scale_translate_xy=values, diagnostic_silhouette_iou=iou,
                        cleanup=stats, **review))
sheet.save(OUT / 'comparison.png')
sheet.resize((1400, 1320), Image.Resampling.NEAREST).save(OUT / 'comparison-enlarged.png')
(OUT / 'processing.json').write_text(json.dumps(dict(raw_sha256=digest(OUT / 'raw.png'),
    raw_size=raw.size, script_sha256=digest(Path(__file__)), matte_sha256=digest(Path(matte.__file__)),
    fitting_sha256=digest(Path(fitting.__file__)), processing_seconds=time.monotonic()-started,
    cells=records), indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ('cell','diagnostic_silhouette_iou','failures')} for r in records]))
