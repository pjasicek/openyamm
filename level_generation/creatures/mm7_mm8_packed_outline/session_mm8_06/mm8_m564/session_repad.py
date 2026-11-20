"""Reprepare one rejected complete sheet inside this session, preserving earlier inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

REPO = Path.cwd().resolve()
STAGE = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm8_06'
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
from prepare_packed_outline import best_grid, native_2x


def repad(family, job_id, padding, reason):
    root = STAGE / family
    out = root / 'redo_2x'
    assert not (out / 'review/acceptance.json').exists(), 'Accepted package is immutable'
    run = json.loads((out / 'run.json').read_text())
    job = next(j for j in run['jobs'] if j['id'] == job_id)
    old = {k: job[k] for k in ['native_crop', 'cell_native_size', 'columns', 'rows',
                             'references', 'reference_roles', 'prompt', 'prepared_assets', 'selected_raw']
           if k in job}
    job.setdefault('preparation_versions', []).append(old)
    if job.get('selected_raw'):
        attempt = next(a for a in job['attempts'] if a.get('raw') == job['selected_raw'])
        attempt.update(status='rejected_after_visual_review', failure_reason=reason)
    sources = json.loads((root / 'sources.json').read_text())
    images = [native_2x(sources['sources'][n], sources, sources['base_palette'])[0]
              for n in job['frames']]
    boxes = [im.getbbox() for im in images]
    crop2 = [min(b[0] for b in boxes) - padding * 2,
             min(b[1] for b in boxes) - padding * 2,
             max(b[2] for b in boxes) + padding * 2,
             max(b[3] for b in boxes) + padding * 2]
    crop = [v / 2 for v in crop2]
    cell = [(crop2[2] - crop2[0]) // 2, (crop2[3] - crop2[1]) // 2]
    budget, _, columns, rows, envelope = best_grid(len(images), *cell)
    colour = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
    outline = Image.new('RGB', colour.size, 'white')
    for i, im in enumerate(images):
        piece = im.crop(crop2)
        check = Image.new('RGBA', im.size)
        check.paste(piece, tuple(crop2[:2]))
        assert np.array_equal(np.array(im), np.array(check))
        xy = (i % columns * piece.width, i // columns * piece.height)
        colour.paste(piece, xy)
        inside = np.array(piece.getchannel('A'))[::2, ::2] > 0
        edge = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
        guide = np.full((*inside.shape, 3), 255, np.uint8)
        guide[edge] = 0
        outline.paste(Image.fromarray(guide).resize(piece.size, Image.Resampling.NEAREST), xy)
    folder = out / 'references' / f'padding_{padding}'
    folder.mkdir(exist_ok=True)
    refs = [folder / (job_id + '_native.png'), folder / (job_id + '_outline.png'),
            REPO / job['references'][2]]
    assert not refs[0].exists() and not refs[1].exists(), 'Preserve prior preparation'
    colour.save(refs[0])
    outline.save(refs[1])
    prompt = (REPO / job['prompt']).read_text()
    prompt = prompt.replace(f"{job['columns']} columns by {job['rows']} rows",
                            f'{columns} columns by {rows} rows')
    prompt = re.sub(r'Shared native-coordinate union crop .*?\n',
        f'Shared native-coordinate union crop {crop} (exclusive right/bottom), cell {cell}, '
        f"actor canvas {sources['logical_canvas']}, pivot {sources['logical_pivot']}. "
        f'Every step has the SAME crop/scale/origin. Never independently center, fit or zoom poses. '
        f'Keep {padding} native pixels of transparent safety padding and every anatomy/equipment tip. '
        f'Fill the planned {columns * cell[0]}:{rows * cell[1]} aspect without oversized margins.\n', prompt)
    prompt = re.sub(r'Request \d+x\d+ or larger',
                    f'Request {round(columns * cell[0] * 2.8)}x{round(rows * cell[1] * 2.8)} or larger', prompt)
    prompt += '\nCOMPLETE-SHEET BOUNDARY CORRECTION: ' + reason + '\n'
    pp = out / 'prompts' / f'{job_id}_padding{padding}_v{len(job["attempts"]) + 1}.txt'
    assert not pp.exists()
    pp.write_text(prompt)
    job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
               observed_envelope=list(envelope), planned_sampling=budget, padding_native_px=padding,
               references=[str(q.relative_to(REPO)) for q in refs],
               prompt=str(pp.relative_to(REPO)), status='prepared_retry_pending')
    job['prepared_assets'] = [dict(path=str(q.relative_to(REPO)),
        sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in refs + [pp]]
    job.pop('selected_raw', None)
    (out / 'run.json').write_text(json.dumps(run, indent=2) + '\n')
    print(json.dumps(dict(family=family, job=job_id, padding=padding, grid=[columns, rows])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    parser.add_argument('job')
    parser.add_argument('padding', type=int)
    parser.add_argument('reason')
    args = parser.parse_args()
    repad(args.family, args.job, args.padding, args.reason)
