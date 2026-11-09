"""Prepare immutable whole-sheet revisions without replacing selected checkpoints."""
import copy
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy import ndimage

from prepare_session import REPO, SESSION, asset, best_grid, native_2x, read, write

REVISIONS = [
    ('mm7_m230', 'standing_2_sheet', 2, 'Material restoration correction: the prior result retained coarse pixel blocks. Repaint the native steel plates with fine scratches, worn brass edges and small separate chainmail rings. Preserve the side-facing helmet and exact original pose. Produce new real material detail with deep native contrast and natural shading.', 'm230fa0'),
    ('mm7_m230', 'standing_3_sheet', 2, 'Material restoration correction: the prior result retained coarse pixel blocks. Repaint the native steel plates with fine scratches, worn brass edges and small separate chainmail rings. Preserve the rear-quarter helmet, back tabard and exact original pose. Produce new real material detail with deep native contrast and natural shading.', 'm230fa0'),
    ('mm7_m230', 'hit_2_sheet', 2, 'Anatomy correction: preserve the pronounced backward torso lean, hip/knee flexion and head tilt in the third native step m230nc2. Keep every step and native joint bend; do not straighten the body. Follow each outline for geometry, while restoring fine steel/chainmail material detail.', 'm230fa0'),
    ('mm7_m242', 'standing_4_sheet', 2, 'Rotation correction: this is the strict REAR view. Show the back of the brown hood and robe exactly as the native silhouette does. The skull face, eye sockets and front ribcage are hidden behind the hood/robe in this view. The appearance reference supplies cloth texture only; its front-facing pose must not be copied.', None),
    ('mm7_m226', 'attack_4_sheet', 6, 'Equipment correction: the previously returned third pose m226ac4 truncated the raised sword. Preserve the full curved sword tip and every native step on one complete sheet. The shared crop has increased transparent padding for all steps; leave a clear transparent margin outside every tip.', 'm226fa0'),
    ('mm7_m226', 'corpse_0_sheet', 2, 'Identity correction: preserve the native short dark swept-back hair and exact resting pose. Do not add a ponytail, hair ribbon or other new accessory. Use the appearance reference only for the same fighter material finish and short hair identity; all pose geometry comes from the native colour and separate outline sheets.', 'm226fa0'),
    ('mm7_m242', 'attack_0_sheet', 2, 'Pose correction: preserve the native foreshortened robe and exact lower-hem position in every step, especially m242ah0. The raised-arm pose has a shorter projected cloth silhouette. Do not lengthen the robe, straighten folds or add legs; retain the exact skeletal finger joints and cloth/bone coverage.', None),
    ('mm7_m242', 'attack_1_sheet', 2, 'Pose correction: preserve the native foreshortened robe and exact lower-hem position in every step, especially m242ad1. The raised-arm pose has a shorter projected cloth silhouette. Do not lengthen the robe, straighten folds or add legs; retain the exact skeletal finger joints and cloth/bone coverage.', None),
]


def prepare(family, job_id, padding, correction, appearance_name):
    root = SESSION / family
    out = root / 'redo_2x'
    run = read(out / 'run.json')
    selected = next(j for j in run['jobs'] if j['id'] == job_id)
    job = copy.deepcopy(selected)
    version = len(job['attempts']) + 1
    revision_path = out / 'review' / f'{job_id}_revision_v{version}.json'
    if revision_path.exists():
        prior = read(revision_path)
        for record in prior['job']['prepared_assets']:
            assert asset(REPO / record['path'])['sha256'] == record['sha256']
        return prior
    sources = read(root / 'sources.json')
    native = {name: native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
              for name in job['frames']}
    boxes = [native[name].getbbox() for name in job['frames']]
    crop2 = [min(box[i] for box in boxes) - padding * 2 if i < 2
             else max(box[i] for box in boxes) + padding * 2 for i in range(4)]
    crop = [v / 2 for v in crop2]
    cell = [(crop2[i + 2] - crop2[i]) // 2 for i in range(2)]
    budget, _, columns, rows, envelope = best_grid(len(boxes), *cell)
    color = Image.new('RGBA', (columns * cell[0] * 2, rows * cell[1] * 2))
    outline = Image.new('RGB', color.size, 'white')
    for i, name in enumerate(job['frames']):
        tile = native[name].crop(crop2)
        position = (i % columns * tile.width, i // columns * tile.height)
        color.paste(tile, position)
        inside = np.array(tile.getchannel('A'))[::2, ::2] > 0
        boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
        guide = np.full((*inside.shape, 3), 255, np.uint8)
        guide[boundary] = 0
        outline.paste(Image.fromarray(guide).resize(tile.size, Image.Resampling.NEAREST), position)
    refs = [out / 'references' / f'{job_id}_{role}_v{version}.png' for role in ('native', 'outline', 'detail')]
    color.save(refs[0])
    outline.save(refs[1])
    if appearance_name:
        registration = read(out / 'registration.json')
        appearance_path = REPO / registration[appearance_name]['clean_path']
    else:
        appearance_path = REPO / selected['appearance_source']['path']
    appearance = Image.open(appearance_path).convert('RGBA')
    appearance.crop(appearance.getbbox()).save(refs[2])
    prompt = (REPO / selected['prompt']).read_text()
    prompt = prompt.replace(f"{selected['columns']} columns by {selected['rows']} rows", f'{columns} columns by {rows} rows')
    prompt = prompt.replace(f"Shared native-coordinate crop {selected['native_crop']}, padded cell {selected['cell_native_size']}",
                            f'Shared native-coordinate crop {crop}, padded cell {cell}')
    prompt = prompt.replace('initial TWO native pixels', f'reviewed {padding} native pixels')
    target = [math.ceil(color.width * 1.4), math.ceil(color.height * 1.4)]
    prompt = re.sub(r'Request \d+x\d+ or greater', f'Request {target[0]}x{target[1]} or greater', prompt)
    prompt += '\nWHOLE-SHEET REVIEW CORRECTION: ' + correction + '\n'
    prompt_path = out / 'prompts' / f'{job_id}_v{version}.txt'
    assert not prompt_path.exists(), 'Do not overwrite an earlier prompt'
    prompt_path.write_text(prompt)
    job.update(native_crop=crop, cell_native_size=cell, columns=columns, rows=rows,
               observed_envelope=list(envelope), planned_sampling=budget, requested_master=target,
               references=[str(p.relative_to(REPO)) for p in refs], prompt=str(prompt_path.relative_to(REPO)),
               appearance_source=asset(appearance_path), prepared_assets=[asset(p) for p in refs + [prompt_path]])
    revision = dict(family=family, job_id=job_id, version=version, padding_native_px=padding,
                    correction=correction, replaces_raw=selected.get('selected_raw'),
                    status='prepared_not_submitted', job=job)
    write(revision_path, revision)
    return revision


if __name__ == '__main__':
    revisions = [prepare(*row) for row in REVISIONS]
    write(SESSION / 'mm7_m214' / 'correction_queue.json', revisions)
    print(json.dumps([dict(family=r['family'], job=r['job_id'], padding=r['padding_native_px']) for r in revisions]))
