"""Assess the retained leather-boots pilot with the worked creature matte and rigid registration.

This batch has no intended magenta materials. Similarity fitting proposes one uniform scale and translation
per complete pair, never separate scaling of boots, anisotropic stretching or silhouette replacement.
The output remains a candidate until measured and visually reviewed by the HUD queue.
"""
import importlib.util
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage, optimize

HERE = Path(__file__).resolve().parent
HUD = HERE.parents[1]
sys.path.insert(0, str(HUD))
from finalize_classification import ROOT, digest, read
from freeze_targets import rendered
import registration


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def transform(image, size, values):
    scale, x, y = values
    return image.transform(size, Image.Transform.AFFINE,
                           (1 / scale, 0, -x / scale, 0, 1 / scale, -y / scale), Image.Resampling.BICUBIC)


def fit(clean, native):
    reference = np.array(native.getchannel('A')) >= 128
    mask = clean.getchannel('A')
    source = np.array(mask) >= 128
    sy, sx = np.nonzero(source)
    ny, nx = np.nonzero(reference)
    scale = np.sqrt(reference.sum() / source.sum())
    x, y = nx.mean() - scale * sx.mean(), ny.mean() - scale * sy.mean()

    def error(values):
        candidate = np.array(transform(mask, native.size, values)) >= 128
        union = (reference | candidate).sum()
        return 1 - (reference & candidate).sum() / max(1, union)

    result = optimize.differential_evolution(error, [(scale * .85, scale * 1.15), (x - 20, x + 20),
                                                    (y - 20, y + 20)], seed=0, popsize=10, maxiter=100)
    return result.x.tolist(), float(1 - result.fun)


def edge_score(image):
    pixels = np.array(image)
    rgb, alpha = pixels[:, :, :3].astype(float), pixels[:, :, 3]
    contour = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= 128) <= 4) | (alpha < 255))
    score = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]) * alpha / 255
    score[~contour] = 0
    return dict(visible_contour_pixels=int(contour.sum()), max_visible_magenta=float(score.max()),
                suspect_pixels_over_16=int((score > 16).sum()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', default='97d1aad8442045269829c7822f92445c')
    parser.add_argument('--output', default='assessment_v1')
    parser.add_argument('--crops', type=json.loads,
                        default=[[0, 100, 450, 630], [450, 60, 800, 570], [820, 280, 1362, 610],
                                 [0, 730, 550, 1090]])
    args = parser.parse_args()
    matte = module('boots_matte', ROOT / 'level_generation/creatures/mm6_goblin/direct_ai_attack/clean_edges.py')
    state = read('checkpoint/state.json')
    attempt = next(a for a in state['attempts'] if a['id'] == args.attempt)
    assert digest(Path(attempt['raw'])) == attempt['sha256']
    job = next(j for j in read('jobs.json')['jobs'] if j['id'] == attempt['job'])
    targets = {t['id']: t for t in read('expected_targets.json')['targets']}
    # Empty gutters inspected in the actual raw master, not assumed from the submitted sheet dimensions.
    crops = args.crops
    assert len(crops) == len(job['members'])
    destination = HERE / args.output
    destination.mkdir(exist_ok=True)
    (destination / 'process_snapshot.py').write_bytes(Path(__file__).read_bytes())
    raw = Image.open(attempt['raw']).convert('RGB')
    records, pairs = [], []
    for member, crop in zip(job['members'], crops):
        target = targets[member['target']]
        clean, stats = matte.extract(raw.crop(crop))
        name = target['runtime_name']
        clean.save(destination / f'{name}-clean-master.png')
        with Image.open(ROOT / member['source_path']) as source:
            native = rendered(source, 'item').resize(tuple(member['export_region'][2:]), Image.Resampling.NEAREST)
        values, iou = fit(clean, native)
        candidate = transform(clean.convert('RGBa'), native.size, values).convert('RGBA')
        artifact = destination / f'{name}.png'
        candidate.save(artifact)
        review = registration.evidence(member, target, artifact, destination / 'registration')
        pairs.append((name, native, candidate))
        records.append(dict(cell=member['id'], raw_crop_xyxy=crop, uniform_scale_translate_xy=values,
                            diagnostic_silhouette_iou=iou, cleanup=stats, master_edges=edge_score(clean),
                            export_edges=edge_score(candidate), artifact=str(artifact.resolve()), **review,
                            status='candidate_awaiting_visual_review'))
    sheet = Image.new('RGB', (900, sum(max(n.height, c.height) + 48 for _, n, c in pairs)), '#777777')
    draw = ImageDraw.Draw(sheet)
    y = 0
    for name, native, candidate in pairs:
        draw.text((8, y), name + ': native | restored | overlay | restored on light / dark', fill='white')
        for x, im, bg in [(8, native, '#555555'), (220, candidate, '#555555'),
                          (432, Image.blend(native, candidate, .5), '#555555'),
                          (644, candidate, '#eeeeee')]:
            tile = Image.new('RGBA', im.size, bg)
            tile.alpha_composite(im)
            sheet.paste(tile.convert('RGB'), (x, y + 24))
        y += native.height + 48
    sheet.save(destination / 'contact.png')
    (destination / 'processing.json').write_text(json.dumps(dict(attempt=attempt['id'], command=sys.argv,
        raw_sha256=attempt['sha256'], script_sha256=digest(Path(__file__)),
        cleanup_script_sha256=digest(Path(matte.__file__)), cells=records), indent=2) + '\n')
    print(json.dumps([{k: r[k] for k in ['cell', 'diagnostic_silhouette_iou', 'failures', 'export_edges']}
                      for r in records], indent=2))


if __name__ == '__main__':
    main()
