"""Sheet of render_clip.py output: review/<tag>/f_NN_<view>.png -> review/<tag>_sheet.png. Args: tag."""
import sys, os, glob
from PIL import Image
tag = sys.argv[1]; d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'review', tag)
frames = sorted({os.path.basename(p).split('_')[1] for p in glob.glob(os.path.join(d, 'f_*_front.png'))}, key=int)
s = Image.new('RGB', (260 * len(frames), 340 * 3), (30, 30, 30))
for i, f in enumerate(frames):
    for k, v in enumerate(('front', 'left', 'three_quarter')):
        s.paste(Image.open(os.path.join(d, f'f_{f}_{v}.png')).convert('RGB'), (i * 260, k * 340))
(s.resize((260 * len(frames) * 2 // 3, 340 * 2)) if len(frames) > 6 else s).save(d + '_sheet.png')
