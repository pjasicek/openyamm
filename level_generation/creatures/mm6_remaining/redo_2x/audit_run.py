"""Check staged generation provenance and alpha delivery without certifying artistic quality."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from prepare_run import REPO


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(project):
    root = REPO / project
    out = root / 'redo_2x'
    run = json.loads((out / 'run.json').read_text())
    required = set(json.loads((root / 'manifest.json').read_text())['frames'])
    generated, rows = set(), []
    for job in run['jobs']:
        raw = job.get('selected_raw')
        if not raw:
            continue
        attempt = next(a for a in job['attempts'] if a['raw'] == raw)
        assert sha(REPO / raw) == attempt['sha256'], raw
        assert sha(REPO / attempt['prompt']) == attempt['prompt_sha256'], attempt['prompt']
        for reference in attempt['references']:
            assert sha(REPO / reference['path']) == reference['sha256'], reference['path']
        image = Image.open(REPO / raw).convert('RGBA')
        alpha = np.array(image)[:, :, 3]
        assert list(image.size) == attempt['actual_size'], raw
        generated.update(job['frames'])
        row = dict(job=job['id'], raw=raw, raw_sha256=attempt['sha256'], size=list(image.size),
                   alpha_extrema=list(image.getchannel('A').getextrema()),
                   background_kind='supplied_alpha' if (alpha < 255).any() else 'opaque_matte',
                   fully_transparent_pixels=int((alpha == 0).sum()),
                   partial_alpha_pixels=int(((alpha > 0) & (alpha < 255)).sum()),
                   near_transparent_pixels=int(((alpha > 0) & (alpha <= 4)).sum()))
        report_path = out / 'review' / (job['id'] + '_extraction.json')
        if report_path.exists():
            report = json.loads(report_path.read_text())
            row['extraction_current'] = report['raw_sha256'] == attempt['sha256']
            if row['extraction_current']:
                row['clean_frames'] = len(report['frames'])
        rows.append(row)
    result = dict(status='generation_provenance_checked; visual and placement acceptance separate',
                  project=project, required_names=len(required), generated_names=len(generated & required),
                  missing_names=sorted(required - generated), unexpected_names=sorted(generated - required),
                  complete_raw_name_coverage=required <= generated,
                  supplied_alpha_sheets=sum(r['background_kind'] == 'supplied_alpha' for r in rows),
                  background_preference='True RGBA transparency; never painted checkerboard',
                  background_check_limit='Alpha statistics prove actual transparency, not absence of painted patterns; '
                                         'inspect each image visually.',
                  sheets=rows)
    (out / 'review/background_delivery.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'sheets'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    audit(parser.parse_args().project)
