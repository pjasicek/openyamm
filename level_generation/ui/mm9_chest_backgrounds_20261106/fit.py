#!/usr/bin/env python3
"""Fit a generated chest background to the chest table's grid (README.md).

Usage: fit.py RAW NAME LEFT TOP RIGHT BOTTOM [--install]
LEFT TOP RIGHT BOTTOM are the generated image's floor edges in its own pixels (measured on the raw image). The image is
scaled separately per axis and placed so that floor lands on the target floor box (the grid plus a 6-unit margin, in
native 460x344 units, written at x2 as 920x688), then saved as final/NAME.png; with --install also over the world's
icons_x2/NAME.png. review/NAME_fit.png shows the result with the grid drawn on it.
"""
import shutil, sys
from pathlib import Path

from PIL import Image, ImageDraw

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
GRID = {'mm9_chest': (42, 34), 'mm9_treasure_bag': (18, 30)}   # chest_data.txt GridOffsetX/Y; 9x9 cells of 32
MARGIN, SCALE, SIZE = 6, 2, (920, 688)


def main() -> int:
    raw, name = Path(sys.argv[1]), sys.argv[2]
    left, top, right, bottom = (float(v) for v in sys.argv[3:7])
    gx, gy = GRID[name]
    target = [(gx - MARGIN) * SCALE, (gy - MARGIN) * SCALE, (gx + 288 + MARGIN) * SCALE, (gy + 288 + MARGIN) * SCALE]
    image = Image.open(raw).convert('RGB')
    sx = (target[2] - target[0]) / (right - left)
    sy = (target[3] - target[1]) / (bottom - top)
    scaled = image.resize((round(image.width * sx), round(image.height * sy)), Image.LANCZOS)
    ox, oy = round(target[0] - left * sx), round(target[1] - top * sy)
    if ox > 0 or oy > 0 or ox + scaled.width < SIZE[0] or oy + scaled.height < SIZE[1]:
        print(f'warning: the scaled image does not cover the canvas (offset {ox},{oy}, size {scaled.size}); '
              'edges are padded from the nearest pixels')
    canvas = Image.new('RGB', SIZE)
    canvas.paste(scaled, (ox, oy))
    # Pad uncovered edges by stretching the nearest covered row or column.
    if ox > 0:
        canvas.paste(canvas.crop((ox, 0, ox + 1, SIZE[1])).resize((ox, SIZE[1])), (0, 0))
    if oy > 0:
        canvas.paste(canvas.crop((0, oy, SIZE[0], oy + 1)).resize((SIZE[0], oy)), (0, 0))
    end_x, end_y = ox + scaled.width, oy + scaled.height
    if end_x < SIZE[0]:
        canvas.paste(canvas.crop((end_x - 1, 0, end_x, SIZE[1])).resize((SIZE[0] - end_x, SIZE[1])), (end_x, 0))
    if end_y < SIZE[1]:
        canvas.paste(canvas.crop((0, end_y - 1, SIZE[0], end_y)).resize((SIZE[0], SIZE[1] - end_y)), (0, end_y))
    (W / 'final').mkdir(exist_ok=True)
    final = W / 'final' / f'{name}.png'
    canvas.save(final)
    review = canvas.copy()
    draw = ImageDraw.Draw(review)
    for i in range(10):
        x, y = (gx + 32 * i) * SCALE, (gy + 32 * i) * SCALE
        draw.line([(x, gy * SCALE), (x, (gy + 288) * SCALE)], fill=(255, 0, 0), width=2)
        draw.line([(gx * SCALE, y), ((gx + 288) * SCALE, y)], fill=(255, 0, 0), width=2)
    review.save(W / 'review' / f'{name}_fit.png')
    if '--install' in sys.argv:
        installed = ROOT / 'assets_dev/worlds/mm9/icons_x2' / f'{name}.png'
        shutil.copyfile(final, installed)
        installed.chmod(0o644)
        print('installed', installed)
    print(final, f'scale {sx:.3f} x {sy:.3f}, offset {ox},{oy}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
