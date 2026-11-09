"""Hash-bound attachment guard and result checkpointing for this isolated session."""
import argparse
import fcntl
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import re

from PIL import Image, ImageDraw

REPO = Path('/home/pjasicek/github/OpenYAMM')
STAGE = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm8_03'
sys.path.insert(0, str(REPO / 'level_generation/creatures'))
from sheet_checks import screen


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def select(stem, count):
    root = STAGE / f'mm8_m{stem}' / 'redo_2x'
    path = root / 'run.json'
    run = json.loads(path.read_text())
    jobs = [job for job in run['jobs'] if job['status'] in ('pending', 'pending_retry')
            and (len(job['references']) == 3 or job['id'] == 'walk_0_sheet')][:count]
    payload = []
    for job in jobs:
        refs = [str((REPO / item).resolve()) for item in job['references']]
        assert 2 <= len(refs) <= 3
        assert re.search(r'_native(?:_v\d+)?\.png$', refs[0])
        assert re.search(r'_outline(?:_v\d+)?\.png$', refs[1])
        assert job['reference_roles'][:2] == ['untouched_native_complete_animation',
                                             'outline_only_geometry_no_shading']
        for asset in job['prepared_assets']:
            assert sha(REPO / asset['path']) == asset['sha256']
        assert Image.open(refs[0]).size == Image.open(refs[1]).size
        prompt = (REPO / job['prompt']).read_text()
        assert prompt.startswith('TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION:')
        attempt = dict(status='submitted', sha256=None, submitted_utc=datetime.now(timezone.utc).isoformat(),
             actual_tool_arguments=dict(referenced_image_paths=refs, transparent_background=True),
             references=[dict(path=item, role=role, sha256=sha(Path(item)))
                         for item, role in zip(refs, job['reference_roles'])],
             prompt=job['prompt'], prompt_sha256=sha(REPO / job['prompt']), bootstrap_exception=len(refs) == 2)
        job['attempts'].append(attempt)
        job['status'] = 'submitted'
        payload.append(dict(stem=stem, job=job['id'], prompt=prompt, refs=refs))
    run['status'] = 'in_progress'
    save(path, run)
    # Inspect submitted images together without modifying the actual attachments.
    if jobs:
        panels = []
        for job in jobs:
            images = [Image.open(REPO / item).convert('RGBA') for item in job['references']]
            for image in images:
                image.thumbnail((740, 700))
            width = max(image.width for image in images[:2])
            panel = Image.new('RGB', (width * 2 + 250, max(image.height for image in images) + 26), '#3b3f43')
            draw = ImageDraw.Draw(panel)
            draw.text((4, 4), f'{stem} {job["id"]}: native | actual matching outline | detail', fill='white')
            panel.paste(images[0], (0, 26), images[0])
            panel.paste(images[1], (width, 26), images[1])
            if len(images) == 3:
                images[2].thumbnail((250, 700))
                panel.paste(images[2], (width * 2, 26), images[2])
            panels.append(panel)
        contacts = []
        for start in range(0, len(panels), 3):
            group = panels[start:start + 3]
            contact = Image.new('RGB', (max(panel.width for panel in group), sum(panel.height for panel in group)), '#3b3f43')
            y = 0
            for panel in group:
                contact.paste(panel, (0, y))
                y += panel.height
            contact_path = root / 'review' / f'submission_inputs_{jobs[start]["id"]}.png'
            contact.save(contact_path)
            contacts.append(str(contact_path))
        print(json.dumps(dict(jobs=payload, contact=contacts[0], contacts=contacts)))
    else:
        print(json.dumps(dict(jobs=[])))


def stage(stem, job_id, source, failure):
    root = STAGE / f'mm8_m{stem}' / 'redo_2x'
    path = root / 'run.json'
    run = json.loads(path.read_text())
    job = next(item for item in run['jobs'] if item['id'] == job_id)
    attempt = job['attempts'][-1]
    assert attempt['status'] == 'submitted'
    if failure:
        attempt.update(status='failed_tool', failure=failure)
        job['status'] = 'failed_tool'
        save(path, run)
        print(json.dumps(dict(stem=stem, job=job_id, failure=failure)))
        return
    destination = root / 'raw' / f'{job_id}_v{len(job["attempts"])}.png'
    recovered = destination.exists()
    if recovered:
        assert source.resolve() == destination.resolve(), 'Never overwrite a returned image'
    else:
        shutil.copy2(source, destination)
    checks = screen(destination, job['cell_native_size'], [job['columns'], job['rows']], len(job['frames']))
    # Preserve shortfall diagnostics; whole cycles can pass only after visual review.
    resolution = [item for item in checks['failures'] if 'below 2x' in item]
    checks['failures'] = [item for item in checks['failures'] if item not in resolution]
    checks['warnings'].extend(resolution)
    attempt.update(status='generated_pending_validation', raw=str(destination.relative_to(REPO)),
                   original_output=str(source), sha256=sha(destination), actual_size=checks['delivered_size'],
                   static_screen=checks)
    if recovered:
        attempt['checkpoint_recovery'] = 'The imagegen return was already staged, but concurrent checkpoint writes before the session lock lost its result entry. Existing raw PNG recovered; no additional imagegen attempt.'
        for candidate in Path('/home/pjasicek/.codex/generated_images').glob('*/exec-*.png'):
            if abs(candidate.stat().st_mtime - destination.stat().st_mtime) < .01 and sha(candidate) == sha(destination):
                attempt['original_output'] = str(candidate)
                break
    job.update(status='partial', selected_raw=str(destination.relative_to(REPO)))
    save(path, run)
    print(json.dumps(dict(stem=stem, job=job_id, raw=str(destination), delivered=checks['delivered_size'],
                         sampling=checks['nominal_grid_sampling_xy'], failures=checks['failures'],
                         warnings=checks['warnings'])))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['select', 'stage', 'recover', 'repack'])
    parser.add_argument('stem', type=int)
    parser.add_argument('--count', type=int, default=3)
    parser.add_argument('--job')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--failure')
    parser.add_argument('--reason')
    parser.add_argument('--padding', type=int, default=6)
    args = parser.parse_args()
    lock_path = STAGE / f'mm8_m{args.stem}' / 'redo_2x' / '.session.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.mode == 'select':
            select(args.stem, args.count)
        elif args.mode == 'stage':
            stage(args.stem, args.job, args.source, args.failure)
        elif args.mode == 'repack':
            sys.path.insert(0, str(REPO/'level_generation/creatures/mm6_remaining/redo_2x'))
            from repack_packed_outline import repack
            from session_prepare import HEADER
            root = STAGE / f'mm8_m{args.stem}'
            repack(str(root.relative_to(REPO)), args.job, args.reason, args.padding)
            path = root/'redo_2x/run.json'; run = json.loads(path.read_text())
            job = next(j for j in run['jobs'] if j['id'] == args.job)
            prompt_path = REPO/job['prompt']; lines = prompt_path.read_text().replace('MM6','MM8').splitlines()
            found = False; selected = []
            for line in lines:
                if line.startswith('Use case:'):
                    if found: continue
                    found = True
                if line.startswith('TASK CONTEXT'): continue
                selected.append(line)
            prompt = HEADER+'\n'+'\n'.join(selected)+'\n'
            prompt = re.sub(r'Request a LARGE \d+x\d+', 'Request a LARGE '+ 'x'.join(map(str,job['requested_master'])), prompt)
            prompt = prompt.replace('Keep 2 native pixels',f'Keep {args.padding} native pixels')
            prompt_path.write_text(prompt)
            job['prepared_assets'] = [dict(path=item,sha256=sha(REPO/item)) for item in [*job['references'],job['prompt']]]
            save(path, run)
        else:
            root = STAGE / f'mm8_m{args.stem}' / 'redo_2x'
            run = json.loads((root / 'run.json').read_text())
            for job in run['jobs']:
                path = root / 'raw' / f'{job["id"]}_v{len(job["attempts"])}.png'
                if job['status'] == 'submitted' and path.exists():
                    stage(args.stem, job['id'], path, None)


if __name__ == '__main__':
    main()
