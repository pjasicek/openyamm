"""Apply reviewed particle ownership corrections around the shared sheet extractor.

The shared extractor retains every alpha pixel, but has no metadata hook for moving
a detached component to another pose. This local operation changes ownership only.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def extract(project):
    repo = Path.cwd()
    root = repo / project
    policy = json.loads((root / 'processing.json').read_text())
    sys.path.insert(0, str(repo / 'level_generation/creatures/mm6_remaining/redo_2x'))
    import extract_run

    shared = extract_run.connected_cells

    def corrected(image, job, **kwargs):
        result = shared(image, job, **kwargs)
        correction = policy.get('component_ownership_overrides', {}).get(job['id'])
        if not correction:
            return result
        raw = repo / job['selected_raw']
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == correction['raw_sha256']
        assert correction['reason']
        sheets = []
        for rect, cell in result:
            full = Image.new('RGBA', image.size)
            full.paste(cell, tuple(rect[:2]))
            sheets.append(np.array(full))
        for move in correction['moves']:
            source = job['frames'].index(move['from'])
            target = job['frames'].index(move['to'])
            x0, y0, x1, y1 = move['raw_rect']
            region = sheets[source][y0:y1, x0:x1]
            destination = sheets[target][y0:y1, x0:x1]
            selected = region[:, :, 3] > 0
            assert not (destination[:, :, 3][selected] > 0).any()
            destination[selected] = region[selected]
            region[selected] = 0
        combined = np.stack(sheets)
        assert np.array_equal(combined.sum(axis=0), np.array(image))
        assert ((combined[:, :, :, 3] > 0).sum(axis=0) <= 1).all()
        corrected_result = []
        for pixels in sheets:
            full = Image.fromarray(pixels)
            x0, y0, x1, y1 = full.getbbox()
            rect = [max(0, x0-12), max(0, y0-12), min(full.width, x1+12), min(full.height, y1+12)]
            corrected_result.append((rect, full.crop(rect)))
        return corrected_result

    extract_run.connected_cells = corrected
    extract_run.extract(project)


if __name__ == '__main__':
    extract(str(Path(__file__).resolve().parent.relative_to(Path.cwd())))
