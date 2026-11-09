#!/usr/bin/env python3
"""Arrange the measured reference plots into six review sheets."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

studyRoot = Path(__file__).resolve().parents[1]
for kind, worlds in json.loads((studyRoot / 'reference_maps.json').read_text()).items():
    for world, names in worlds.items():
        for suffix, label in [('', 'Measured plans'), ('_blender', 'Blender inspection lighting')]:
            paths = [studyRoot / f'evidence/{world}/{name}{suffix}.png' for name in names]
            if not all(path.exists() for path in paths):
                continue
            fig, axes = plt.subplots(2,3,figsize=(18,12))
            for ax, name, path in zip(axes.flat,names,paths):
                with Image.open(path) as source:
                    ax.imshow(source)
                ax.set_title(name)
                ax.axis('off')
            axes.flat[5].axis('off')
            axes.flat[5].text(.1,.5,f'{world.upper()} {kind} references\n{label}; not game screenshots',fontsize=17)
            fig.tight_layout()
            fig.savefig(studyRoot / f'evidence/{world}_{kind}{suffix}_overview.png',dpi=100)
            plt.close(fig)
