"""Assemble a restored ink pair over hash-bound accepted page pixels; require subsequent visual review."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
HUD = HERE.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest, read
from freeze_targets import rendered
import registration

spec = importlib.util.spec_from_file_location('creature_edges',
    ROOT / 'level_generation/creatures/mm6_goblin/direct_ai_attack/clean_edges.py')
edges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edges)


def color_landmarks(image):
    a = np.asarray(image.convert('RGB'), dtype=float)
    green = (a[:, :, 1] > a[:, :, 0] * 1.12) & (a[:, :, 1] > a[:, :, 2] * 1.08)
    green[:, 130:] = False
    green[:130, :] = False
    green[220:, :] = False
    yy, xx = np.nonzero(green)
    return dict(green_centroid=[float(xx.mean()), float(yy.mean())],
                green_bounds=[int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shift', type=float, nargs=2, default=[0, 0])
    args = parser.parse_args()
    out = args.output.resolve()
    assert not out.exists(), 'Use a fresh directory; retain reviewed evidence'
    out.mkdir(parents=True)
    attempt = HUD / 'checkpoint/attempts' / args.attempt
    payload = json.loads((attempt / 'payload.json').read_text())
    assert payload['spell_ink_matte'] and len(payload['selected_cells']) == 2
    job = next(j for j in read('jobs.json')['jobs'] if j['id'] == payload['job'])
    targets = {t['id']: t for t in read('expected_targets.json')['targets']}
    raw = Image.open(attempt / 'raw.png').convert('RGB')
    clean, cleanup = edges.extract(raw)
    clean.save(out / 'cleaned-master.png')
    layout = payload['execution_layout']
    clean = clean.convert('RGBa').resize(tuple(layout['canvas_size']), Image.Resampling.LANCZOS).convert('RGBA')
    crop = payload['page_crops'][0]
    page_path = Path(crop['full_page'])
    assert digest(page_path) == crop['page_sha256'], 'Accepted page changed'
    page = Image.open(page_path).convert('RGBA')
    x, y, w, h = crop['final_draw_xywh']
    substrate = page.crop((x, y, x + w, y + h))
    cells = []
    contact = Image.new('RGB', (1080, 650), '#555555')
    draw = ImageDraw.Draw(contact)
    for index, cell in enumerate(payload['selected_cells']):
        member = next(m for m in job['members'] if m['id'] == cell)
        target = targets[member['target']]
        a, b, cw, ch = layout['cell_rects'][cell]
        ink = clean.crop((a, b, a + cw, b + ch))
        ink = ink.convert('RGBa').transform(ink.size, Image.Transform.AFFINE,
            (1, 0, -args.shift[0], 0, 1, -args.shift[1]), Image.Resampling.BICUBIC).convert('RGBA')
        ink.save(out / (target['runtime_name'] + '-ink.png'))
        native = rendered(Image.open(ROOT / member['source_path']), 'hud').resize((cw, ch), Image.Resampling.NEAREST)
        assembled = substrate.copy()
        assembled.alpha_composite(ink)
        # Native key rectangles reserve overlapping spell areas. They are a canvas contract, not a fitted art mask.
        key = np.asarray(native.getchannel('A')) == 0
        ink_a = np.asarray(ink.getchannel('A'))
        overlap = int(((ink_a >= 16) & key).sum())
        assembled.putalpha(native.getchannel('A'))
        artifact = out / (target['runtime_name'] + '.png')
        assembled.save(artifact)
        evidence = registration.evidence(member, target, artifact, out / 'registration')
        full = page.copy()
        full.alpha_composite(assembled, (x, y))
        full.save(out / (target['runtime_name'] + '-page.png'))
        for column, (label, picture) in enumerate([('native', native), ('restored', assembled),
                                                  ('ink on dark', ink), ('ink on light', ink)]):
            px, py = column * 270, index * 325
            draw.text((px, py), target['runtime_name'] + ' ' + label, fill='white')
            bg = Image.new('RGBA', picture.size, '#222222' if column != 3 else '#eeeeee')
            bg.alpha_composite(picture)
            contact.paste(bg.convert('RGB'), (px, py + 24))
        cells.append(dict(cell=cell, evidence=evidence, ink_pixels_in_native_key=overlap,
            native_color_landmarks=color_landmarks(native), restored_color_landmarks=color_landmarks(assembled),
            exact_page_pixels_outside_ink=bool(np.array_equal(np.asarray(assembled)[:, :, :3][ink_a == 0],
                                                            np.asarray(substrate)[:, :, :3][ink_a == 0]))))
    contact.save(out / 'pair-review.png')
    (out / 'process_snapshot.py').write_bytes(Path(__file__).read_bytes())
    report = dict(attempt=args.attempt, raw_sha256=digest(attempt / 'raw.png'), cleanup=cleanup,
        cleanup_script_sha256=digest(Path(edges.__file__)), page_sha256=crop['page_sha256'],
        shift_x2=args.shift, cells=cells, status='awaiting_visual_review')
    (out / 'processing.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(cells, indent=2))


if __name__ == '__main__':
    main()
