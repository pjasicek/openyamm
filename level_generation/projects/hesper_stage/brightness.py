"""Mean brightness of a map's review captures (the integrator's readability gate, 2026-10-23).

Usage: python3 level_generation/projects/hesper_stage/brightness.py <review dir> [<review dir> ...]
Reads every PNG below each directory, crops the HUD away (the outer 10 % at the sides, the top 12 % and the bottom 28 %)
and prints the mean, median and darkest shot's mean luminance (0-255). Targets: Kreegan maps a mean of 40 or more,
colony maps 55 or more, and no shot under 20 unless the document asks for a blackout.
"""
import sys
from pathlib import Path

from PIL import Image, ImageStat


def luminance(path):
    image = Image.open(path).convert('L')
    width, height = image.size
    return ImageStat.Stat(image.crop((int(width * 0.1), int(height * 0.12), int(width * 0.9),
                                      int(height * 0.72)))).mean[0]


for folder in sys.argv[1:]:
    shots = sorted(Path(folder).rglob('*.png'))
    if not shots:
        print(f'{folder}: no shots')
        continue
    values = {shot.relative_to(folder).as_posix(): luminance(shot) for shot in shots}
    ordered = sorted(values.values())
    dark = [name for name, value in values.items() if value < 20]
    print(f'{folder}: {len(ordered)} shots, mean {sum(ordered) / len(ordered):.1f}, '
          f'median {ordered[len(ordered) // 2]:.1f}, darkest {ordered[0]:.1f}'
          + (f'; under 20: {", ".join(sorted(dark))}' if dark else ''))
