"""Town review sheets: concept A | original | result for every concept pose, and before/after contact sheets.

  python3 source/town_compare.py review/town_original review/<run>

Concepts are concepts/<shot>_A.png (Codex edits of review/town_original/<shot>.png). Writes review/town_<run>/.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]


def label(draw, x, y, text):
    draw.rectangle([x, y, x + 8 + 9 * len(text), y + 22], fill=(0, 0, 0))
    draw.text((x + 4, y + 3), text, fill=(255, 255, 0), font_size=16)


def main():
    original, result = Path(sys.argv[1]), Path(sys.argv[2])
    out = PROJECT / 'review' / f'town_{result.name}'
    out.mkdir(parents=True, exist_ok=True)
    w, h = 800, 450
    for concept in sorted((PROJECT / 'concepts').glob('*_A.png')):
        shot = concept.name[:-6]
        before, after = original / f'{shot}.png', result / f'{shot}.png'
        if not before.exists() or not after.exists():
            continue
        sheet = Image.new('RGB', (w, h * 3 + 8), (0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for row, (path, text) in enumerate(((concept, 'concept A'), (before, 'original'), (after, 'result'))):
            sheet.paste(Image.open(path).convert('RGB').resize((w, h)), (0, row * (h + 4)))
            label(draw, 0, row * (h + 4) + 30, f'{text} {shot}')
        sheet.save(out / f'concept_{shot}.jpg', quality=88)
    shots = sorted(p.name for p in result.glob('*.png') if (original / p.name).exists())
    tw, th = 400, 225
    for part in range(0, len(shots), 12):
        group = shots[part:part + 12]
        sheet = Image.new('RGB', (tw * 4, th * 6), (0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for i, name in enumerate(group):
            for k, folder in enumerate((original, result)):
                x, y = ((i % 2) * 2 + k) * tw, (i // 2) * th
                sheet.paste(Image.open(folder / name).convert('RGB').resize((tw, th)), (x, y))
                label(draw, x, y, ('before ' if k == 0 else 'after ') + name[:-4])
        sheet.save(out / f'pairs_{part // 12:02d}.jpg', quality=85)
    print(out)


if __name__ == '__main__':
    main()
