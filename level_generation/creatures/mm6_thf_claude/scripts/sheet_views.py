"""Compose review/<tag>/fNN_<view>.png into review/<tag>_sheet.png (rows = views, columns = frames). Args: tag views"""
import sys, os, glob
from PIL import Image
tag, views = sys.argv[1], sys.argv[2].split(',')
d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', tag)
frames = sorted({os.path.basename(p)[1:3] for p in glob.glob(os.path.join(d, 'f*_*.png'))})
ims = {(f, v): Image.open(os.path.join(d, f'f{f}_{v}.png')).convert('RGB') for f in frames for v in views}
W, H = next(iter(ims.values())).size
s = Image.new('RGB', (W * len(frames), H * len(views)))
for i, f in enumerate(frames):
    for j, v in enumerate(views):
        s.paste(ims[(f, v)], (i * W, j * H))
s.save(d + '_sheet.png')
