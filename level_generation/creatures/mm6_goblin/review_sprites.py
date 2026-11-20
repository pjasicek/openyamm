"""Separate labeled contact sheets and native-size PNG/indexed comparisons for visual delivery review."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent / 'spritesheets'
BG = (43, 47, 48, 255)


def over_background(image):
    result = Image.new('RGBA', image.size, BG)
    result.alpha_composite(image)
    return result.convert('RGB')


def build():
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    for clip in manifest['clips']:
        # Four frames per page row preserve useful review size, all poses and all eight real directions.
        for first in range(0, clip['count'], 4):
            frames = clip['frames'][first:first + 4]
            page = Image.new('RGB', (4 * 244, 8 * 215), BG[:3])
            draw = ImageDraw.Draw(page)
            for row in range(8):
                for col, frame in enumerate(frames):
                    name = frame['texture_stem'] + str(row)
                    with Image.open(ROOT / 'png_355x289' / (name + '.png')) as source:
                        tile = over_background(source).resize((244, 199), Image.Resampling.LANCZOS)
                    page.paste(tile, (244 * col, 215 * row + 16))
                    draw.text((244 * col + 4, 215 * row + 2), name, fill='white')
            page.save(ROOT / 'previews' / f"{clip['name'].lower()}_contact_{first:02}.png")
    selected = ['rgobsa0', 'rgobsa2', 'rgobsa4', 'rgobwh1', 'rgobag0', 'rgobag6', 'rgobdl3', 'rgobca7']
    page = Image.new('RGB', (710, len(selected) * 313), BG[:3])
    draw = ImageDraw.Draw(page)
    for row, name in enumerate(selected):
        png = Image.open(ROOT / 'png_355x289' / (name + '.png')).convert('RGBA')
        bmp = Image.open(ROOT / 'bmp_355x289' / (name + '.bmp'))
        indexed = bmp.convert('RGBA')
        indexed.putalpha(Image.frombytes('L', bmp.size, bytes(255 if p else 0 for p in bmp.tobytes())))
        for col, (label, picture) in enumerate([('RGBA PNG', png), ('Indexed BMP', indexed)]):
            page.paste(over_background(picture), (col * 355, row * 313 + 24))
            draw.text((col * 355 + 5, row * 313 + 5), name + ' / ' + label + ' / native size', fill='white')
    page.save(ROOT / 'previews' / 'png_bmp_native_size.png')
    print('Saved all-frame, all-direction contacts and native-size PNG/BMP comparison')


if __name__ == '__main__':
    build()
