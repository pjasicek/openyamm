"""Insert local imagegen road-join corrections, preserving the rest of each pilot."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import importlib.util
import json
from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import splu
from common import *
from compose_pilot import mask

FOLDER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('donor_metrics', T / 'mm7/check.py')
checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)


def insert(original, painted, domain):
    indices = np.full(domain.shape, -1, int); indices[domain] = np.arange(domain.sum())
    rows, columns = np.where(domain)
    matrix = lil_matrix((len(rows), len(rows))); matrix.setdiag(4)
    rhs = np.zeros((len(rows), 3))
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        sy, sx = (rows + dy) % 512, (columns + dx) % 512
        adjacent = indices[sy, sx]; valid = adjacent >= 0
        matrix[np.arange(len(rows))[valid], adjacent[valid]] = -1
        rhs += painted[rows, columns] - painted[sy, sx]
        rhs[~valid] += original[sy[~valid], sx[~valid]]
    result = original.copy()
    result[domain] = splu(matrix.tocsc()).solve(rhs)
    return np.clip(result, 0, 255)


def main():
    reports = []
    sheet = Image.new('RGB', (1024, 560), '#202933'); draw = ImageDraw.Draw(sheet)
    yy, xx = np.mgrid[:512, :512]
    for row, name in enumerate(('drsrew', 'drsrns')):
        original = read(FOLDER / 'authoring' / (name + '.png'))
        axis = 1 if name.endswith('ew') else 0
        shifted = np.roll(original, 256, axis=axis)
        guide_path = FOLDER / 'inputs' / (name + '_join_offset.png')
        assert np.array_equal(read(guide_path), shifted), 'Imagegen input differs from current pilot'
        painted = read(FOLDER / 'raw' / (name + '_join_repair.png'), 512)
        old_mask = mask(shifted if axis == 1 else shifted.transpose(1, 0, 2))
        new_mask = mask(painted if axis == 1 else painted.transpose(1, 0, 2))
        if axis == 0: old_mask, new_mask = old_mask.T, new_mask.T
        domain = (abs((xx if axis == 1 else yy) - 255.5) < 96) & (distance_transform_edt(~(old_mask | new_mask)) < 20)
        result = insert(shifted, painted, domain)
        assert np.array_equal(result[~domain], shifted[~domain])
        result = np.roll(result, -256, axis=axis)
        save(FOLDER / 'donors/authoring' / (name + '.png'), result)
        reduced = seams.reduce(seams.pad(result, 'wrap'))
        save(FOLDER / 'donors/runtime' / (name + '.png'), reduced)
        final_mask = mask(result if axis == 1 else result.transpose(1, 0, 2))
        if axis == 0: final_mask = final_mask.T
        save(FOLDER / 'donors/masks' / (name + '.png'), final_mask * 255)
        side = 'E' if axis == 1 else 'S'
        metrics, joined, _ = checker.metrics(reduced, reduced, side)
        before = read(FOLDER / 'runtime_pilots' / (name + '.png'))
        if axis == 0: before = before.transpose(1, 0, 2)
        for col, im in enumerate((np.concatenate([before, before], 1), joined)):
            sheet.paste(Image.fromarray(seams.byte(im)), (col * 512, row * 280 + 24))
            draw.text((col * 512 + 4, row * 280 + 5), name + (' before' if col == 0 else ' local join repair'), fill='white')
        reports.append(dict(name=name, join=metrics, protected_fraction=float(np.mean(~domain)),
                            input_sha256=sha(guide_path), raw_sha256=sha(FOLDER / 'raw' / (name + '_join_repair.png')),
                            authoring_sha256=sha(FOLDER / 'donors/authoring' / (name + '.png')),
                            runtime_sha256=sha(FOLDER / 'donors/runtime' / (name + '.png'))))
    sheet.save(FOLDER / 'donors/repeat_comparison.png')
    (FOLDER / 'donors/build.json').write_text(json.dumps(dict(status='candidate_donors_require_visual_review', tiles=reports), indent=2) + '\n')
    print(json.dumps(reports, indent=2))


if __name__ == '__main__': main()
