"""Prepare a replacement complete sheet for a demonstrated pose/layout fault; preserve submitted versions."""
import argparse
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image
from scipy import ndimage

from prepare_packed_outline import best_grid, native_2x


def repack(project, job_id, reason, padding=6):
    root = Path(project)
    out = root/'redo_2x'
    with (out/'.stage.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        run = json.loads((out/'run.json').read_text())
        job = next(job for job in run['jobs'] if job['id'] == job_id)
        assert reason and job['attempts'], 'Replacement requires a submitted trial and a specific fault'
        version = len(job['attempts'])+1
        old_prompt = Path(job['prompt']).read_text()
        keys = ('native_crop', 'cell_native_size', 'columns', 'rows', 'references', 'prompt', 'prepared_assets')
        job.setdefault('preparation_history', []).append({key: job[key] for key in keys})
        sources = json.loads((root/'sources.json').read_text())
        images = [native_2x(sources['sources'][name], sources, sources['base_palette'])[0] for name in job['frames']]
        boxes = [image.getbbox() for image in images]
        crop = [min(b[0] for b in boxes)-padding*2, min(b[1] for b in boxes)-padding*2,
                max(b[2] for b in boxes)+padding*2, max(b[3] for b in boxes)+padding*2]
        cell = [(crop[2]-crop[0])//2, (crop[3]-crop[1])//2]
        budget, _, columns, rows, envelope = best_grid(len(images), *cell)
        native = Image.new('RGBA', (columns*cell[0]*2, rows*cell[1]*2))
        outline = Image.new('RGB', native.size, 'white')
        for index, image in enumerate(images):
            part = image.crop(crop)
            offset = (index % columns*part.width, index//columns*part.height)
            native.paste(part, offset)
            inside = np.array(part.getchannel('A'))[::2, ::2] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3, 3), bool))
            guide = np.full((*inside.shape, 3), 255, np.uint8)
            guide[boundary] = 0
            outline.paste(Image.fromarray(guide).resize(part.size, Image.Resampling.NEAREST), offset)
        paths = [out/'references'/f'{job_id}_{role}_v{version}.png' for role in ('native', 'outline')]
        for image, path in zip((native, outline), paths):
            image.save(path)
        count = len(images)
        first = (f"Use case: style-transfer. Output EXACTLY {count} sprites in ONE image: {columns} columns, "
                 f"{rows} rows, chronological row-major order. This is the COMPLETE original MM6 {job['action']} "
                 f"animation for stored view {job['view']}. The original contains precisely {count} bitmap steps. "
                 "Do not add poses, interpolation, repeated subjects, a longer cycle or extra panels.\n")
        prompt = first+old_prompt.split('\n', 1)[1]
        prompt += '\nCorrection required in the complete returned sheet: ' + reason + '\n'
        layout = (f"Layout: chronological row-major order {', '.join(job['frames'])}. Common native crop "
                  f"{[value/2 for value in crop]}, padded cell {cell}, original actor canvas "
                  f"{sources['logical_canvas']} and pivot {sources['logical_pivot']}. Exactly {columns} columns and "
                  f"{rows} rows. Keep the shared native position/scale for every step and {padding} native pixels "
                  "of transparent padding at each cell edge and all four sheet edges. No extremity may touch a "
                  "cell or sheet boundary. No independent centering, zoom, silhouette fit or body stretching.")
        prompt = re.sub(r'^Layout:.*$', lambda _: layout, prompt, flags=re.M)
        colour = (f"Palette/material separation: Generate ONLY native base palette {sources['base_palette']} "
                  "shown in Image 1 and described above; preserve those exact material colours. No alternative "
                  "palette colours. Image 3 supplies fine finish only, never alternate colours or geometry.")
        prompt = re.sub(r'^Palette/material separation:.*$', lambda _: colour, prompt, flags=re.M)
        target = [math.ceil(columns*cell[0]*2.8), math.ceil(rows*cell[1]*2.8)]
        prompt = re.sub(r'Request a LARGE \d+x\d+ master', f'Request a LARGE {target[0]}x{target[1]} master', prompt)
        if count == 1:
            prompt += '\nFINAL FRAME COUNT: ONE SINGLE SPRITE. Match the one native bitmap and its one outline. No storyboard, walk cycle, variations, repeated character or extra panels.\n'
        prompt += '\nPreserve every original step on this ONE returned sheet. Transparent alpha only outside subjects and in original gaps; no floor, gradient, cast shadow or background decoration.\n'
        prompt_path = out/'prompts'/f'{job_id}_v{version}.txt'
        prompt_path.write_text(prompt)
        job.update(native_crop=[value/2 for value in crop], cell_native_size=cell, columns=columns, rows=rows,
                   observed_envelope=envelope, planned_sampling=budget, requested_master=target,
                   references=[str(path) for path in paths]+[job['references'][2]], prompt=str(prompt_path),
                   padding_native_px=padding, status='pending_retry', retry_reason=reason)
        for attempt in job['attempts']:
            if attempt.get('raw') == job.get('selected_raw'):
                attempt.update(review_status='rejected_visual_review', rejection_reason=reason)
        job.pop('selected_raw', None)
        job['prepared_assets'] = [dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
                                  for path in [*job['references'],job['prompt']]]
        (out/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    print(json.dumps(dict(project=str(root),id=job_id,version=version,reason=reason)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('job')
    parser.add_argument('--reason', required=True)
    parser.add_argument('--padding', type=int, default=6)
    args = parser.parse_args()
    assert args.padding >= 1
    repack(args.project, args.job, args.reason, args.padding)
