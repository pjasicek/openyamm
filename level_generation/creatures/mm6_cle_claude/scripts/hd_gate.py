"""HD master gate sheet: selected masters next to the native standing views at the same figure height.

Usage: python3 scripts/hd_gate.py <out.png> <master.png>...   (run from the project directory)
"""
import sys

from PIL import Image

NATIVE = '../mm6_cle/native/clesta{}.png'
HEIGHT = 900


def crop_alpha(image):
    image = image.convert('RGBA')
    box = image.getchannel('A').point(lambda a: 255 if a > 16 else 0).getbbox()
    return image.crop(box)


def fit(image):
    image = crop_alpha(image)
    return image.resize((max(1, round(image.width * HEIGHT / image.height)), HEIGHT), Image.LANCZOS)


def main():
    out = sys.argv[1]
    tiles = [fit(Image.open(NATIVE.format(view))) for view in range(5)]
    tiles += [fit(Image.open(path)) for path in sys.argv[2:]]
    width = sum(tile.width for tile in tiles) + 40 * (len(tiles) + 1)
    sheet = Image.new('RGBA', (width, HEIGHT + 80), (48, 48, 48, 255))
    x = 40
    for tile in tiles:
        sheet.alpha_composite(tile, (x, 40))
        x += tile.width + 40
    sheet.convert('RGB').save(out)


if __name__ == '__main__':
    main()
