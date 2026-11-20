"""Plot draft native-sprite envelopes and actual terrain contours; not a gameplay render."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import numpy as np

from author_props import ground_at
from prepare_natural_entrances import world

PROJECT = Path(__file__).resolve().parent


def render():
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    data = json.loads((PROJECT/'review/clearing_proposal.json').read_text())
    height = (PROJECT/'landscape/heightmap.raw').read_bytes()
    fig, axes = plt.subplots(1, 2, figsize=(12, 8))
    for ax, site in zip(axes, data['sites']):
        building = next(b for b in spec['buildings'] if b['id'] == site['id'])
        xs, ys = np.linspace(-1200, 1200, 97), np.linspace(-600, 1800, 97)
        z = np.array([[ground_at(height, world({**building, 'padHeight': 0}, [float(x), float(y), 0]))
                       for x in xs] for y in ys])
        contours = ax.contour(xs, ys, z, levels=9, colors='#6d745b', linewidths=.6, alpha=.6)
        ax.clabel(contours, fontsize=7, fmt='%g')
        x0, y0, x1, y1 = site['clearApproach']
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, facecolor='#e6ddb2', edgecolor='#98832a', alpha=.65))
        ax.text((x0+x1)/2, -380, 'clear approach', ha='center', fontsize=8)
        if site['futureGrowingGround']:
            x0, y0, x1, y1 = site['futureGrowingGround']
            ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, facecolor='none', edgecolor='#a26827', linestyle='--'))
            ax.text(300, -80, 'future crop\nempty', fontsize=8, color='#865018')
        for row in site['records']:
            x, y = row['localPoint']
            tree = row['name'].startswith('tree')
            color = '#36632c' if tree else '#84796c' if row['name'].startswith('rock') else '#a0447c'
            ax.add_patch(Circle((x, y), row['visualRadius'], facecolor=color, edgecolor=color, alpha=.18))
            ax.scatter([x], [y], s=25 if tree else 12, color=color)
            offset = (-180, -100) if site['id'] == 'nibbler' and row['name'] == 'plant17' else (26, 25)
            ax.text(x+offset[0], y+offset[1], row['name']+'\nZ'+str(row['position'][2]), fontsize=8)
            if row['proposedInteraction']:
                ax.scatter([x], [y], s=100, facecolors='none', edgecolors='#cf3e25', linewidths=2)
        ax.set(xlim=(-1200, 1200), ylim=(-600, 1800), aspect='equal',
               xlabel='Local X (native units)', ylabel='Local depth (north)')
        ax.set_title(site['id'].capitalize()+' — proposed grove', fontweight='bold')
        ax.set_facecolor('#f0f1e8')
    fig.suptitle('Measured clearing proposal — not exported or visually accepted\n'
                 'Circles: sprite half-width envelopes; red ring: proposed placeholder stump', fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, .92])
    fig.savefig(PROJECT/'review/clearing_proposal.png', dpi=120)
    plt.close(fig)


if __name__ == '__main__':
    render()
