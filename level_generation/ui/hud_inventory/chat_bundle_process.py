"""Portable candidate extraction. Run from an extracted bundle; never accepts artwork automatically."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import fitting
import matte


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def footprint(native, restored):
    results = {}
    for threshold in (16, 128):
        a = np.array(native.getchannel('A')) >= threshold
        b = np.array(restored.getchannel('A')) >= threshold
        features = []
        for mask in (a, b):
            y, x = np.nonzero(mask)
            if not len(x):
                return {'pass': False, 'reason': 'Unexpected blank foreground'}
            features.append((np.array([x.min(), y.min(), x.max()+1, y.max()+1]),
                             np.array([x.mean(), y.mean()])))
        bounds = float(np.max(np.abs(features[0][0] - features[1][0])))
        centroid = float(np.max(np.abs(features[0][1] - features[1][1])))
        area = float(b.sum() / a.sum())
        iou = float((a & b).sum() / (a | b).sum())
        results[str(threshold)] = dict(bounds_error=bounds, centroid_error=centroid,
            area_ratio=area, iou=iou, passed=bounds <= 2 and centroid <= 2 and .9 <= area <= 1.1 and iou >= .85)
    return dict(thresholds=results, passed=all(r['passed'] for r in results.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sheet', help='Stable sheet ID, e.g. S001')
    parser.add_argument('raw', type=Path, help='Actual saved imagegen output for this sheet')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text())
    sheet = next(s for s in manifest['sheets'] if s['id'] == args.sheet)
    layout = json.loads((root / sheet['layout']).read_text())
    raw = Image.open(args.raw).convert('RGB')
    width, height = layout['reference_size']
    assert abs(raw.width / raw.height - width / height) < .02, 'Unexpected aspect ratio: inspect actual grid first'
    sx, sy = raw.width / width, raw.height / height
    out = root / 'outputs' / 'processed' / args.sheet
    out.mkdir(parents=True, exist_ok=False)
    max_width = max(c['x2_size'][0] for c in layout['cells'])
    max_height = max(c['x2_size'][1] for c in layout['cells'])
    columns = min(3, len(layout['cells']))
    card_width, card_height = 2*max_width + 30, 2*max_height + 85
    proof = Image.new('RGB', (columns*card_width, math.ceil(len(layout['cells'])/columns)*card_height), '#454545')
    draw = ImageDraw.Draw(proof)
    records = []
    for i, cell in enumerate(layout['cells']):
        source = root / cell['native_png']
        assert sha(source) == cell['rendered_png_sha256'], 'Native reference changed'
        native = Image.open(source).convert('RGBA').resize(tuple(cell['x2_size']), Image.Resampling.NEAREST)
        opaque = cell['member']['cleanup'] == 'opaque_canvas'
        x, y, w, h = cell['native_canvas_rect'] if opaque else cell['slot_rect']
        rect = (round(x*sx), round(y*sy), round((x+w)*sx), round((y+h)*sy))
        if opaque:
            clean = raw.crop(rect).convert('RGBA')
            cleanup = dict(mode='opaque_registered_rectangle',
                           note='No key removal or foreground fitting. Review internal facial landmarks and framing.')
            values, iou = None, None
            restored = clean.resize(tuple(cell['x2_size']), Image.Resampling.LANCZOS)
        else:
            clean, cleanup = matte.extract(raw.crop(rect))
            values, iou = fitting.fit(clean, native)
            restored = fitting.transform(clean.convert('RGBa'), native.size, values).convert('RGBA')
        clean.save(out / (cell['id'] + '-clean-master.png'))
        artifact = out / (cell['id'] + '.png')
        restored.save(artifact)
        assert list(restored.size) == cell['x2_size']
        px, py = i % columns * card_width, i // columns * card_height
        draw.text((px+5, py+5), cell['id'], fill='white')
        for dx, dy, im, bg, label in (
                (5, 40, native, '#454545', 'Native x2'), (max_width+20, 40, restored, '#454545', 'Candidate x2'),
                (5, max_height+75, restored, '#eeeeee', 'Light'),
                (max_width+20, max_height+75, restored, '#111111', 'Dark')):
            draw.text((px+dx, py+dy-15), label, fill='white')
            tile = Image.new('RGBA', im.size, bg)
            tile.alpha_composite(im)
            proof.paste(tile.convert('RGB'), (px+dx, py+dy))
        records.append(dict(id=cell['id'], status='needs_visual_review', artifact=artifact.name,
            artifact_sha256=sha(artifact), size=list(restored.size), raw_crop_xyxy=rect,
            uniform_scale_translate=values, fitting_iou=iou, cleanup=cleanup,
            footprint=footprint(native, restored), landmarks=[],
            pending='Actual full-sheet/cell/light-dark/internal-landmark/identity review; never auto-accept'))
    proof.save(out / 'comparison.png')
    (out / 'processing.json').write_text(json.dumps(dict(sheet=args.sheet, raw_sha256=sha(args.raw),
        raw_size=list(raw.size), cells=records), indent=2)+'\n')
    print(json.dumps(dict(sheet=args.sheet, candidates=len(records), directory=str(out), accepted=0)))


if __name__ == '__main__':
    main()
