"""Writes Meshy Smart Topology job files for Hesper item designs (classification.json), never submits them: the
integrator submits through tools/creature_meshy.py (P4.md, 2026-10-24).

  batch <n> <icon> [icon ...]   per icon: meshy/<icon>/references_hd/00_three_quarter.png (the icon's selected 1254 px
                                Codex original, or `master` in classification.json overridden by an image given as
                                icon=path), its binary-alpha copy 00_three_quarter_meshy.png and
                                meshy/requests/<icon>_st_v1.json (untextured, 3,000 target, 5 credits); records the
                                batch in meshy/batches.json
Usage: python3 -I meshy_jobs.py batch 1 hes_survey_helm hes_mag_boots ..."""
import hashlib
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ART = os.path.join(REPO, 'design', 'kreegan_world', 'art', 'item_icons')
MESHY = os.path.join(HERE, 'meshy')
CREDITS = 5


def sha256(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_job(icon, source):
    folder = os.path.join(MESHY, icon, 'references_hd')
    os.makedirs(folder, exist_ok=True)
    image = Image.open(source).convert('RGBA')
    image.save(os.path.join(folder, '00_three_quarter.png'))
    image.putalpha(image.split()[3].point(lambda value: 255 if value >= 100 else 0))
    meshy_input = os.path.join(folder, '00_three_quarter_meshy.png')
    image.save(meshy_input)
    request = {'image_url': f'@file:{icon}/references_hd/00_three_quarter_meshy.png', 'ai_model': 'meshy-t2',
               'model_type': 'smart-topology', 'target_polycount': 3000, 'should_texture': False,
               'target_formats': ['glb']}
    os.makedirs(os.path.join(MESHY, 'requests'), exist_ok=True)
    with open(os.path.join(MESHY, 'requests', f'{icon}_st_v1.json'), 'w') as handle:
        json.dump(request, handle, indent=1)
        handle.write('\n')
    return {'icon': icon, 'job': f'{icon}_st_v1', 'request': f'requests/{icon}_st_v1.json', 'credits': CREDITS,
            'source': os.path.relpath(source, REPO), 'meshy_input_sha256': sha256(meshy_input)}


def batch(number, targets):
    designs = json.load(open(os.path.join(HERE, 'classification.json')))
    ledger_path = os.path.join(MESHY, 'batches.json')
    ledger = json.load(open(ledger_path)) if os.path.exists(ledger_path) else {'ceiling': 405, 'batches': []}
    queued = {job['icon'] for entry in ledger['batches'] if entry['batch'] != number for job in entry['jobs']}
    jobs = []
    for target in targets:
        icon, _, override = target.partition('=')
        assert designs[icon]['route'] == 'meshy', icon
        assert icon not in queued, f'{icon} is already in a batch'
        jobs.append(write_job(icon, override or os.path.join(ART, designs[icon]['master'])))
    ledger['batches'] = [entry for entry in ledger['batches'] if entry['batch'] != number]
    ledger['batches'].append({'batch': number, 'status': 'written, not submitted', 'jobs': jobs,
                              'credits': CREDITS * len(jobs)})
    with open(ledger_path, 'w') as handle:
        json.dump(ledger, handle, indent=1)
        handle.write('\n')
    print(f'batch {number}: {len(jobs)} jobs, {CREDITS * len(jobs)} credits')


def main():
    if sys.argv[1] != 'batch':
        raise SystemExit(__doc__)
    batch(int(sys.argv[2]), sys.argv[3:])


main()
