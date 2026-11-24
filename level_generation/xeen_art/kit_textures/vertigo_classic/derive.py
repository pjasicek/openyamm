#!/usr/bin/env python3
"""The pieces of the Vertigo classic kits cut from the generated ones, no new image (finished/ at x4, _x2, _x1).

  <v>cornr  post_right: the corner bay (<v>corn) mirrored left to right
  <v>gable  gable:      the plain bay's middle square (half posts at the sides, plaster between), 128 x 128
  <v>ridge  ridge:      the beam (<v>beam, 64 x 32, grain along) turned upright, 32 x 64, as MM7's trim2_32

  python3 derive.py [xva xvb]
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
FINISHED = HERE / 'finished'


def save(image, name):
    image.save(FINISHED / f'{name}.png')
    image.resize((image.width // 2, image.height // 2), Image.LANCZOS).save(FINISHED / f'{name}_x2.png')
    image.resize((image.width // 4, image.height // 4), Image.LANCZOS).save(FINISHED / f'{name}_x1.png')
    print(name, image.size)


def main():
    for prefix in sys.argv[1:] or ['xva', 'xvb']:
        corner = Image.open(FINISHED / f'{prefix}corn.png')
        save(corner.transpose(Image.FLIP_LEFT_RIGHT), f'{prefix}cornr')
        wall = Image.open(FINISHED / f'{prefix}wall.png')
        side = wall.width
        top = (wall.height - side) // 2
        save(wall.crop((0, top, side, top + side)), f'{prefix}gable')
        beam = Image.open(FINISHED / f'{prefix}beam.png')
        save(beam.transpose(Image.ROTATE_90), f'{prefix}ridge')


if __name__ == '__main__':
    main()
