#!/usr/bin/env python3
"""Cut the gong picture (finished/xngong.png, 192 x 192 map units at the gong) into the six slab strips the gong's
slabs show (xngong1 the top slab, 96 wide, to xngong6 the bottom one): each strip is the slab's window of the
picture, resampled to 128 x 32 texels (x4: 512 x 128) and stretched once over its slab (`fit`)."""
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
gong = Image.open(HERE / 'finished/xngong.png').convert('RGB')
px = gong.width / 192.0
# Top to bottom: slab bases 640 .. 480 (rise 32), widths 96, 160, 192, 192, 160, 96, centred; picture top z = 672.
for number, (width, base) in enumerate(((96, 640), (160, 608), (192, 576), (192, 544), (160, 512), (96, 480)), 1):
    x0, x1 = (96 - width / 2) * px, (96 + width / 2) * px
    y0, y1 = (672 - (base + 32)) * px, (672 - base) * px
    strip = gong.crop((round(x0), round(y0), round(x1), round(y1))).resize((512, 128), Image.LANCZOS)
    strip.save(HERE / f'finished/xngong{number}.png')
    strip.resize((256, 64), Image.LANCZOS).save(HERE / f'finished/xngong{number}_x2.png')
    strip.resize((128, 32), Image.LANCZOS).save(HERE / f'finished/xngong{number}_x1.png')
    print(f'xngong{number}', width, base)
