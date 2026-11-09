"""Review uninstalled straight-road pilots; expose unfinished longitudinal joins."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import importlib.util
import json
from PIL import ImageDraw
from scipy.ndimage import binary_fill_holes, label
from common import *

FOLDER = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('road_pilot_metrics', T / 'mm7/check.py')
check = importlib.util.module_from_spec(spec); spec.loader.exec_module(check)
records = []
sheet = Image.new('RGB', (1024, 560), '#202933'); draw = ImageDraw.Draw(sheet)
for row, name in enumerate(('drsrew', 'drsrns')):
    path = FOLDER / 'runtime_pilots' / (name + '.png')
    rgb = read(path)
    side = 'E' if name.endswith('ew') else 'S'
    metrics, joined, start = check.metrics(rgb, rgb, side)
    coverage = read(FOLDER / 'masks' / (name + '.png'))[:, :, 0] > 127
    _, components = label(coverage)
    holes = int(np.sum(binary_fill_holes(coverage) & ~coverage))
    records.append(dict(name=name, runtime_sha256=sha(path), axis=side, self_join=metrics,
                        connected_components=components, interior_hole_pixels=holes,
                        visual_acceptance=False, reason='Finished border continuity and native road review remain pending'))
    original = read(P / 'references' / (name + '.png'), 256)
    if side == 'S': original = original.transpose(1, 0, 2)
    for col, im in enumerate((np.concatenate([original, original], 1), joined)):
        sheet.paste(Image.fromarray(seams.byte(im)), (col * 512, row * 280 + 24))
        draw.text((col * 512 + 4, row * 280 + 4), name + (' native repeat' if col == 0 else ' pilot repeat'), fill='white')
sheet.save(FOLDER / 'pilot_repeats.png')
(FOLDER / 'pilot_validation.json').write_text(json.dumps(dict(status='pilot_screening_not_acceptance', tiles=records), indent=2) + '\n')
print(json.dumps(records, indent=2))
