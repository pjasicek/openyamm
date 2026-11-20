"""Locate remaining material joins and measure the current Xeen rim without modifying active source."""
from collections import Counter
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import numpy as np
from PIL import Image

from geography import CLASS_COLORS

PROJECT = Path(__file__).resolve().parent
OUTPUT = PROJECT / 'review/landscape_boundaries_v1'


def study():
    OUTPUT.mkdir(exist_ok=True)
    classes_path = PROJECT / 'landscape/surface_classes.png'
    height_path = PROJECT / 'landscape/heightmap.raw'
    classes = np.array(Image.open(classes_path))[:127, :127]
    heights = np.frombuffer(height_path.read_bytes(), dtype=np.uint8).reshape(128, 128) * 32.0
    corners = np.stack([heights[:-1, :-1], heights[:-1, 1:], heights[1:, :-1], heights[1:, 1:]], axis=-1)
    assignment = json.loads((PROJECT / 'implementation/terrain_assignment.json').read_text())
    unresolved = assignment['unresolvedBoundaryCells']
    counts = Counter(record['family'] for record in unresolved)
    void = classes == 0
    sloping_void = void & (np.ptp(corners, axis=-1) > 0)
    report = {
        'status': 'Read-only source landscape boundary study; no native acceptance or active terrain changes',
        'sourceSha256': {str(path.relative_to(PROJECT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in [classes_path, height_path]},
        'unresolvedBoundaryCounts': dict(counts),
        'voidCells': int(void.sum()),
        'flatVoidCells': int((void & ~sloping_void).sum()),
        'slopingVoidCells': np.argwhere(sloping_void).tolist(),
        'voidHeightRange': [float(corners[void].min()), float(corners[void].max())],
        'profiles': [],
        'implications': [
            'The 347 excluded boundary cells are three distinct problems, not 347 desert/scorched joins.',
            'Only 26 void quads slope, at shared river vertices. Rock paint on sloping void alone cannot finish the rim.',
            'Most land meets a zero-height void edge. A visible rocky rim needs a deliberate land-edge treatment.',
            'Keep river/Acid Pond planes and travel bounds; do not replace the void with invented water.',
            'Scorched boundary cells lie in the outermost northern row; desert also enters the travel crop.'
        ]
    }
    figure, axes = plt.subplots(2, 2, figsize=(15, 12), constrained_layout=True)
    ax = axes[0, 0]
    ax.imshow(classes, cmap=ListedColormap(CLASS_COLORS), vmin=0, vmax=10, interpolation='nearest')
    for family, color in [('mm5void', '#f25b91'), ('7sand', '#eab600'), ('plntyl', '#a40000')]:
        cells = np.array([r['cell'] for r in unresolved if r['family'] == family])
        ax.scatter(cells[:, 1], cells[:, 0], s=8, c=color, label=f'{family}: {len(cells)}')
    ax.add_patch(Rectangle((15.5, 15.5), 96, 96, fill=False, edgecolor='cyan', linewidth=1.5))
    ax.set(title='Source classes and unresolved boundaries; cyan = travel envelope', xlabel='Native column', ylabel='Native row')
    ax.legend(loc='lower right', fontsize=8)
    ax = axes[0, 1]
    ax.imshow(np.where(void, np.ptp(corners, axis=-1), np.nan), cmap='magma', vmin=0, vmax=256)
    cells = np.argwhere(sloping_void)
    ax.scatter(cells[:, 1], cells[:, 0], s=12, c='cyan', label='26 non-flat void cells')
    ax.set(title='Void relief: 4,784 flat quads; slopes only at river contact', xlabel='Native column', ylabel='Native row')
    ax.legend(loc='upper right', fontsize=8)
    for ax, name, direction, fixed, first, last in [
        (axes[1, 0], 'River/wreck: Y = -13,312', 'east', 90, 16, 40),
        (axes[1, 1], 'Falista setting: X = -13,312', 'south', 38, 96, 120)
    ]:
        nodes = list(range(first, last + 1))
        values = [float(heights[fixed, n] if direction == 'east' else heights[n, fixed]) for n in nodes]
        families = [int(classes[fixed, n] if direction == 'east' else classes[n, fixed]) for n in nodes[:-1]]
        for index, family in enumerate(families):
            ax.axvspan(nodes[index], nodes[index + 1], color=CLASS_COLORS[family], alpha=.45)
        ax.plot(nodes, values, 'k.-', label='Actual quantized supporting vertices')
        ax.axhline(0, color='black', linewidth=.6)
        ax.set(title=name, xlabel='Native column' if direction == 'east' else 'Native row', ylabel='Native Z', ylim=(-64, 1200))
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
        report['profiles'].append({'name': name, 'direction': direction, 'fixedIndex': fixed,
                                   'indices': nodes, 'heights': values, 'cellClasses': families})
    figure.savefig(OUTPUT / 'boundaries.png', dpi=130)
    plt.close(figure)
    (OUTPUT / 'measurements.json').write_text(json.dumps(report, indent=2) + '\n')
    print({'unresolved': dict(counts), 'voidCells': int(void.sum()), 'slopingVoidCells': int(sloping_void.sum())})


if __name__ == '__main__':
    study()
