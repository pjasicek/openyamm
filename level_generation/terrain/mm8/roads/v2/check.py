"""Screen available road candidates, all compatible joins and solid road masks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import importlib.util
import json
import argparse
from scipy.ndimage import binary_fill_holes, label
from PIL import ImageDraw
from common import *

parser = argparse.ArgumentParser()
parser.add_argument('--version', choices=['v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13'], default='v2')
args = parser.parse_args()
FOLDER = Path(__file__).resolve().parent.parent / args.version
spec = importlib.util.spec_from_file_location('road_metrics', T / 'mm7/check.py')
checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
build = json.loads((FOLDER / 'build.json').read_text())
images, contracts, masks = {}, {}, []
for record in build['tiles']:
    name = record['name']; group = record['family']
    path = FOLDER / 'runtime' / (name + '.png')
    assert sha(path) == record['runtime_sha256']
    images[name] = read(path)
    substrate = 'dirt' if group == 'roads_dirt' else 'grey_dirt'
    contracts[name] = {s: group if opened else substrate for s, opened in record['topology'].items()}
    alpha = read(FOLDER / 'masks' / (name + '.png'))[:, :, 0] > 127
    _, components = label(alpha)
    holes = int(np.sum(binary_fill_holes(alpha) & ~alpha))
    masks.append(dict(name=name, components=components, holes=holes, passed=components == 1 and holes == 0))
for name in ('dirt', 'grey_dirt'):
    images[name] = read(M / 'runtime' / (name + '.png'))
    contracts[name] = dict.fromkeys('NSEW', name)
results, worst = [], []
for a in sorted(images):
    for b in sorted(images):
        for side, opposite in [('E', 'W'), ('S', 'N')]:
            if contracts[a][side] != contracts[b][opposite]: continue
            metrics, joined, start = checker.metrics(images[a], images[b], side)
            score = max(metrics['boundary_p95'] / max(metrics['interior_p95'], 1e-6), metrics['boundary_max'] / max(metrics['interior_p999'], 1e-6))
            results.append(dict(a=a, side=side, b=b, score=score, **metrics))
            worst.append((score, a + ' ' + side + ' ' + b, joined)); worst = sorted(worst, key=lambda r: -r[0])[:8]
sheet = Image.new('RGB', (1024, 4 * 280), '#202933'); draw = ImageDraw.Draw(sheet)
for i, (score, title, joined) in enumerate(worst):
    x, y = i % 2 * 512, i // 2 * 280
    draw.text((x + 4, y + 4), title + ' relative %.2f' % score, fill='white')
    sheet.paste(Image.fromarray(seams.byte(joined)), (x, y + 24))
sheet.save(FOLDER / 'worst_joins.png')
report = dict(status='partial_road_screening', compatible_checks=len(results), failures=[r for r in results if not r['passed']], checks=results, masks=masks, missing=build['missing'], build_sha256=sha(FOLDER / 'build.json'))
(FOLDER / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(len(results), 'joins;', len(report['failures']), 'failures; bad masks', [m for m in masks if not m['passed']])
print([(r['a'],r['side'],r['b'],round(r['score'],2)) for r in report['failures'][:8]])
