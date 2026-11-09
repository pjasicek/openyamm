"""Keys each tier's Codex paint (<tier>/paint_a.png) and fits it into the MM9 book icon canvas at x2, like the other
MM9 icons (level_generation/ui/mm9_item_icons_20261104/scripts/finish.py: the book family's 144 x 128 box), and writes
the enlarged copy on magenta the texture brief takes (<tier>/icon_x8.png = the x2 icon at 4x).
Outputs per tier: <tier>/icon_x2.png and icon_x8.png.
Usage: python3 -I finish.py [tier ...]"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mm9_item_icons_20261104', 'scripts'))
import finish as icon_finish  # noqa: E402

BOX_X2 = (144, 128)
for tier in sys.argv[1:] or ('normal', 'expert', 'master', 'grandmaster'):
    folder = os.path.join(HERE, tier)
    x2 = icon_finish.fit(icon_finish.key(os.path.join(folder, 'paint_a.png')), BOX_X2)
    x2.save(os.path.join(folder, 'icon_x2.png'))
    x8 = Image.new('RGBA', (x2.width * 4, x2.height * 4), (255, 0, 255, 255))
    x8.alpha_composite(x2.resize(x8.size, Image.LANCZOS))
    x8.convert('RGB').save(os.path.join(folder, 'icon_x8.png'))
    print(tier, x2.size)
