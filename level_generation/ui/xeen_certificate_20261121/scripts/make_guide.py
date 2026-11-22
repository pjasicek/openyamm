"""The layout guide and reference images for the World of Xeen completion certificate (A4, 2026-11-21).
The certificate is drawn in 640 x 480 units (world.yml `completion.layout`); the painting is made on a 1536 x 1024
canvas whose middle 1365 x 1024 is the certificate (grey bars left and right, as original_x2's restorations), later
cut and resized to 1280 x 960. Layout as MM6's 6winbg: title lettering at the top, the subtitle plaque at the bottom,
text zone x 100-540, y 80-410, the OpenYAMM mark centred at (320, 422).
Usage: python3 -I scripts/make_guide.py"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
S = 1365 / 640
X0 = (1536 - 1365) // 2


def box(x0, y0, x1, y1):
    return [X0 + x0 * S, y0 * S, X0 + x1 * S, y1 * S]


def main():
    guide = Image.new('RGB', (1536, 1024), (128, 128, 128))
    draw = ImageDraw.Draw(guide)
    draw.rectangle(box(0, 0, 640, 480), fill=(236, 226, 200))
    draw.rectangle(box(0, 0, 640, 480), outline=(120, 90, 40), width=6)
    draw.rectangle(box(28, 28, 612, 452), outline=(120, 90, 40), width=3)       # inner edge of the knotwork frame
    draw.rectangle(box(150, 8, 490, 70), outline=(0, 150, 0), width=5)          # title lettering
    draw.rectangle(box(100, 80, 540, 410), outline=(220, 0, 0), width=5)        # text zone: kept pale and quiet
    draw.ellipse(box(300, 402, 340, 442), outline=(0, 0, 220), width=5)         # the OpenYAMM mark: plain parchment
    draw.rectangle(box(170, 438, 470, 470), outline=(0, 150, 0), width=5)       # subtitle plaque
    guide.save(HERE / 'guide.png')
    src = REPO / 'reference/mm4_5_world_of_xeen/unpacked/images/intro'
    for name in ('eg270001', 'eg280001', 'eg140001'):
        Image.open(src / f'{name}.raw.png').convert('RGB').resize((960, 600), Image.NEAREST).save(
            HERE / 'refs' / f'{name}.png')
    for name in ('6winbg', '7winbg'):
        Image.open(REPO / f'assets_dev/engine/icons_x2/{name}.png').convert('RGB').save(HERE / 'refs' / f'{name}.png')


main()
