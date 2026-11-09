"""Retain intentional purple in the Lich Jar while extracting its opaque magenta matte."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
HUD = HERE.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest, read
from freeze_targets import rendered
import matte
import registration


def main():
    spec = importlib.util.spec_from_file_location('boots_registration', HERE.parent / 'boots/process.py')
    fitting = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fitting)
    attempt = next(a for a in read('checkpoint/state.json')['attempts'] if a['id'] == 'f0c7d44202bf405cb0fd164310e66fb1')
    member = next(j for j in read('jobs.json')['jobs'] if j['id'] == attempt['job'])['members'][0]
    target = next(t for t in read('expected_targets.json')['targets'] if t['id'] == member['target'])
    out = HERE / 'assessment_v1'
    out.mkdir(exist_ok=True)
    raw = Image.open(attempt['raw']).convert('RGB')
    assert digest(Path(attempt['raw'])) == attempt['sha256']
    clean, settings = matte.extract(raw)
    clean.save(out / 'clean-master.png')
    native = rendered(Image.open(ROOT / member['source_path']), 'item').resize(tuple(target['x2_size']),
                                                                           Image.Resampling.NEAREST)
    transform, iou = fitting.fit(clean, native)
    final = fitting.transform(clean.convert('RGBa'), native.size, transform).convert('RGBA')
    artifact = out / '7item259.png'
    final.save(artifact)
    result = registration.evidence(member, target, artifact, out / 'registration')
    record_path = Path(result['registration_record'])
    record = json.loads(record_path.read_text())
    record['processing'] = dict(attempt=attempt['id'], raw_sha256=attempt['sha256'], matting=settings,
                                uniform_scale_translate_xy=transform, diagnostic_silhouette_iou=iou,
                                note='No global purple desaturation or whole-interior chroma cap.')
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    sheet = Image.new('RGB', (native.width * 10, native.height * 10 + 48), '#666666')
    draw = ImageDraw.Draw(sheet)
    for index, (label, image, color) in enumerate([
            ('Native light', native, '#eeeeee'), ('Native dark', native, '#171717'),
            ('Restored light', final, '#eeeeee'), ('Restored dark', final, '#171717')]):
        tile = Image.new('RGBA', image.size, color)
        tile.alpha_composite(image)
        x, y = index % 2 * native.width * 5, index // 2 * (native.height * 5 + 24)
        draw.text((x, y), label, fill='white')
        sheet.paste(tile.convert('RGB').resize((native.width * 5, native.height * 5),
                                              Image.Resampling.NEAREST), (x, y + 24))
    sheet.save(out / 'edges.png')
    (out / 'process_snapshot.py').write_bytes(Path(__file__).read_bytes())
    (out / 'processing.json').write_text(json.dumps(record['processing'], indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
