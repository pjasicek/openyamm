"""Move extraction seams only through verified empty matte; retain native nominal origins."""
import argparse
import json
import numpy as np
from PIL import Image
from process import ROOT, extract, save


def seam(occupied, nominal, radius):
    empty = ~occupied
    starts = np.where(np.diff(np.r_[False, empty, False].astype(int)) == 1)[0]
    ends = np.where(np.diff(np.r_[False, empty, False].astype(int)) == -1)[0]
    candidates = []
    for a, b in zip(starts, ends):
        if b - a < 8:
            continue
        position = int(np.clip(round(nominal), a + 4, b - 4))
        if abs(position - nominal) < radius:
            candidates.append((abs(position - nominal), position, [int(a), int(b)]))
    assert candidates, ('No safe empty seam', nominal, radius)
    _, position, band = min(candidates)
    return int(position), band


def run(key):
    data = json.loads((ROOT / 'compact_jobs.json').read_text())
    job = data['jobs'][key]
    raw = Image.open(ROOT / job.get('selected_raw', 'raw/' + key + '_v1.png'))
    alpha = np.asarray(extract(raw, job['frames'][0]))[:, :, 3]
    columns, rows = job['columns'], job['rows']
    ys = [0]
    evidence = []
    for row in range(1, rows):
        position, band = seam(np.any(alpha > 0, axis=1), row * raw.height / rows, .23 * raw.height / rows)
        ys.append(position)
        evidence.append({'axis': 'y', 'empty_band': band, 'position': position})
    ys.append(raw.height)
    rectangles = {}
    for row in range(rows):
        xs = [0]
        for col in range(1, columns):
            position, band = seam(np.any(alpha[ys[row]:ys[row + 1]] > 0, axis=0),
                                  col * raw.width / columns, .23 * raw.width / columns)
            xs.append(position)
            evidence.append({'axis': 'x', 'row': row, 'empty_band': band, 'position': position})
        xs.append(raw.width)
        for col in range(columns):
            index = row * columns + col
            if index < len(job['frames']):
                rectangles[job['frames'][index]] = [xs[col], ys[row], xs[col + 1], ys[row + 1]]
    job['extraction_overrides'] = rectangles
    job['extraction_empty_seams'] = evidence
    job['extraction_review'] = 'Only verified empty >=8px matte bands separate reviewed whole poses. Nominal origins and uniform sampling remain unchanged.'
    save(ROOT / 'compact_jobs.json', data)
    print(key, 'saved', len(evidence), 'empty seam proofs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('jobs', nargs='+')
    for key in parser.parse_args().jobs:
        run(key)
