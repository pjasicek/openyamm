"""Session-only complete-sheet preparation repair; preserve every submitted input."""
import argparse
import copy
import math
import re

import numpy as np
from PIL import Image
from scipy import ndimage

from prepare_session import REPO, SESSION, best_grid, native, read, rel, sha, write


def enlarge(family, job_id, padding, reason):
    root = SESSION / family
    run = read(root / 'run.json')
    job = next(j for j in run['jobs'] if j['id'] == job_id)
    assert padding > job['padding_native_px'] and reason
    version = len(job['attempts']) + 1
    old = copy.deepcopy({key: job[key] for key in (
        'native_crop', 'cell_native_size', 'columns', 'rows', 'references', 'prepared_assets',
        'padding_native_px', 'prompt', 'prompt_sha256')})
    job.setdefault('preparation_history', []).append(dict(old, reason=reason))
    images = [native(root, name) for name in job['frames']]
    boxes = [im.getbbox() for im in images]
    crop = [min(b[0] for b in boxes) - padding, min(b[1] for b in boxes) - padding,
            max(b[2] for b in boxes) + padding, max(b[3] for b in boxes) + padding]
    cell = [crop[2] - crop[0], crop[3] - crop[1]]
    sampling, _, columns, rows, envelope = best_grid(len(images), *cell)
    colour = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
    outline = Image.new('RGB', colour.size, 'white')
    for i, im in enumerate(images):
        pixels = np.array(im)
        pixels[pixels[:, :, 3] == 0] = 0
        im = Image.fromarray(pixels)
        piece = im.crop(crop)
        restored = Image.new('RGBA', im.size)
        restored.paste(piece, crop[:2])
        assert np.array_equal(im, restored)
        xy = (i % columns * cell[0] * 2, i // columns * cell[1] * 2)
        colour.paste(piece.resize(tuple(v * 2 for v in cell), Image.Resampling.NEAREST), xy)
        inside = np.asarray(piece.getchannel('A')) > 0
        boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
        guide = np.full((*inside.shape, 3), 255, np.uint8)
        guide[boundary] = 0
        outline.paste(Image.fromarray(guide).resize(tuple(v * 2 for v in cell), Image.Resampling.NEAREST), xy)
    paths = [root / f'references/{job_id}_native_v{version}.png',
             root / f'references/{job_id}_outline_v{version}.png']
    colour.save(paths[0])
    outline.save(paths[1])
    prompt = (REPO / job['prompt']).read_text()
    prompt = prompt.replace(f"{old['columns']} columns by {old['rows']} rows",
                            f'{columns} columns by {rows} rows')
    prompt = re.sub(r'shared whole-animation union crop .*?padding\.',
        f'shared whole-animation union crop {crop} (exclusive right/bottom), cell size {cell} '
        f'and {padding}-native-pixel alpha padding.', prompt)
    requested = [math.ceil(columns * cell[0] * 2.8), math.ceil(rows * cell[1] * 2.8)]
    prompt = re.sub(r'Request a large \d+x\d+ master',
                    f'Request a large {requested[0]}x{requested[1]} master', prompt)
    prompt += ('\nCOMPLETE-SHEET EDGE REPAIR: ' + reason + '. Preserve the enlarged shared transparent '
               'padding in every cell and around the sheet. Every original frame remains together; '
               'never crop a flame tip, limb, face or soft alpha fringe.\n')
    prompt_path = root / f'prompts/{job_id}_v{version}.txt'
    prompt_path.write_text(prompt)
    for index, path in enumerate(paths):
        job['references'][index] = rel(path)
        job['prepared_assets'][index].update(path=rel(path), sha256=sha(path))
    job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
               padding_native_px=padding, planned_sampling=sampling, observed_envelope=list(envelope),
               requested_size=requested, prompt=rel(prompt_path), prompt_sha256=sha(prompt_path),
               status='retry_prepared')
    job['attempts'][-1]['visual_screen'] = dict(status='rejected', reason=reason)
    write(root / 'run.json', run)
    print(f'{family} {job_id}: preserved old inputs; new complete {columns}x{rows} grid, '
          f'{padding}px native padding, {len(images)} original steps')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('job')
    parser.add_argument('padding', type=int)
    parser.add_argument('reason')
    args = parser.parse_args()
    enlarge(args.family, args.job, args.padding, args.reason)
