"""Apply reviewed component ownership when detached effects cross empty gutters.

Every delivered foreground pixel remains unchanged and belongs to exactly one
complete-sheet cell. Shared extraction, alpha cleanup and reports are reused.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
import extract_run


def extract(project, job_id):
    root = REPO / project
    policy = json.loads((root / 'redo_2x/processing.json').read_text())['reviewed_component_ownership'][job_id]
    original = extract_run.connected_cells

    def reviewed_cells(delivered, job, **kwargs):
        assert job['id'] == job_id and policy['reason']
        assert hashlib.sha256((REPO / job['selected_raw']).read_bytes()).hexdigest() == policy['raw_sha256']
        original_cells = original(delivered, job, **kwargs)
        canvases = []
        for rectangle, image in original_cells:
            full = Image.new('RGBA', delivered.size)
            full.paste(image, rectangle[:2])
            canvases.append(np.array(full))
        for move in policy['moves']:
            x0, y0, x1, y1 = move['raw_rect']
            source = canvases[move['from_cell']][y0:y1, x0:x1]
            target = canvases[move['to_cell']][y0:y1, x0:x1]
            selected = source[:, :, 3] > 0
            assert not np.any(target[:, :, 3][selected]), 'Effect pixels already assigned'
            target[selected] = source[selected]
            source[selected] = 0
        pixels = np.array(delivered)
        assert sum(int((array[:, :, 3] > 0).sum()) for array in canvases) == int((pixels[:, :, 3] > 0).sum())
        reconstructed = np.zeros_like(pixels)
        result = []
        for array in canvases:
            selected = array[:, :, 3] > 0
            assert not np.any(reconstructed[:, :, 3][selected])
            reconstructed[selected] = array[selected]
            image = Image.fromarray(array)
            x0, y0, x1, y1 = image.getbbox()
            rectangle = [max(0, x0-12), max(0, y0-12), min(image.width, x1+12), min(image.height, y1+12)]
            result.append((rectangle, image.crop(rectangle)))
        assert np.array_equal(reconstructed[:, :, 3], pixels[:, :, 3]), 'Delivered alpha changed'
        visible = pixels[:, :, 3] > 0
        assert np.array_equal(reconstructed[visible], pixels[visible]), 'Visible delivered RGBA changed'
        return result

    extract_run.connected_cells = reviewed_cells
    try:
        extract_run.extract(project, [job_id])
    finally:
        extract_run.connected_cells = original


if __name__ == '__main__':
    extract(sys.argv[1], sys.argv[2])
