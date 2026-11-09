"""Assemble a restored ink pair over hash-bound accepted page pixels; require subsequent visual review."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, signal

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


def match_landmarks(native, restored):
    patches = {'green_glyph': (25, 145, 72, 64), 'top_small_glyph': (40, 216, 34, 26),
        'bottom_glyph_1': (38, 244, 36, 34), 'bottom_glyph_2': (76, 248, 34, 30),
        'bottom_glyph_3': (111, 248, 36, 30), 'bottom_glyph_4': (147, 247, 38, 31),
        'shield_hilt': (208, 130, 46, 40), 'shield_top': (145, 67, 52, 48)}
    n, r = [ndimage.gaussian_filter(np.asarray(i.convert('L'), dtype=float), .65) for i in (native, restored)]
    r = np.pad(r, 4, mode='edge')
    points, matches = [], []
    for name, (x, y, w, h) in patches.items():
        template, search = n[y:y + h, x:x + w], r[y:y + h + 8, x:x + w + 8]
        z, ones = template - template.mean(), np.ones(template.shape)
        scores = signal.correlate2d(search, z, mode='valid')
        total = signal.correlate2d(search, ones, mode='valid')
        squares = signal.correlate2d(search * search, ones, mode='valid')
        scores /= np.sqrt(np.maximum(squares - total * total / template.size, 1e-8) * (z * z).sum())
        iy, ix = np.unravel_index(scores.argmax(), scores.shape)
        dx, dy = int(ix) - 4, int(iy) - 4
        points.append(dict(name=name, source_xy=[(x + w / 2) / 2, (y + h / 2) / 2],
                           restored_xy=[x + w / 2 + dx, y + h / 2 + dy]))
        matches.append(dict(name=name, reference_patch_x2=[x, y, w, h], measured_shift_x2=[dx, dy],
                            normalized_correlation=float(scores[iy, ix])))
    return points, matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shift', type=float, nargs=2, default=[0, 0])
    parser.add_argument('--second-shift', type=float, nargs=2)
    parser.add_argument('--ink-opacity', type=float, default=1)
    args = parser.parse_args()
    assert 0 < args.ink_opacity <= 1
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
        shift = args.second_shift if index == 1 and args.second_shift else args.shift
        ink = ink.convert('RGBa').transform(ink.size, Image.Transform.AFFINE,
            (1, 0, -shift[0], 0, 1, -shift[1]), Image.Resampling.BICUBIC).convert('RGBA')
        ink.putalpha(ink.getchannel('A').point(lambda value: round(value * args.ink_opacity)))
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
        native_for_matching = Image.open(ROOT / member['source_path']).convert('RGB').resize(
            (cw, ch), Image.Resampling.BICUBIC)
        points, matches = match_landmarks(native_for_matching, assembled)
        record_path = Path(evidence['registration_record'])
        record = json.loads(record_path.read_text())
        record.update(landmarks=points, patch_matches=matches,
            landmark_method='Local normalized correlation of actual native bicubic x2 grayscale patches; inspect visually')
        record_path.write_text(json.dumps(record, indent=2) + '\n')
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
        cells.append(dict(cell=cell, evidence=evidence, ink_pixels_in_native_key=overlap, shift_x2=shift,
            patch_matches=matches,
            native_color_landmarks=color_landmarks(native), restored_color_landmarks=color_landmarks(assembled),
            exact_page_pixels_outside_ink=bool(np.array_equal(np.asarray(assembled)[:, :, :3][ink_a == 0],
                                                            np.asarray(substrate)[:, :, :3][ink_a == 0]))))
    contact.save(out / 'pair-review.png')
    (out / 'process_snapshot.py').write_bytes(Path(__file__).read_bytes())
    report = dict(attempt=args.attempt, raw_sha256=digest(attempt / 'raw.png'), cleanup=cleanup,
        cleanup_script_sha256=digest(Path(edges.__file__)), page_sha256=crop['page_sha256'],
        ink_opacity=args.ink_opacity, cells=cells, status='awaiting_visual_review')
    (out / 'processing.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(cells, indent=2))


if __name__ == '__main__':
    main()
