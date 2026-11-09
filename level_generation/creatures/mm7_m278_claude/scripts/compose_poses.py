"""Join pose_sheet.py renders into one sheet: a row per action (front over side). Args: <dir> <out png> <n> <action...>"""
import sys, os
from PIL import Image, ImageDraw
d, out, n = sys.argv[1], sys.argv[2], int(sys.argv[3]); acts = sys.argv[4:]
W = H = 160
S = Image.new('RGB', (W * n, (2 * H + 14) * len(acts)), (255, 255, 255)); dr = ImageDraw.Draw(S)
for r, act in enumerate(acts):
    y = r * (2 * H + 14); dr.text((2, y), act, fill=(0, 0, 0))
    for k in range(n):
        for j, v in enumerate(('front', 'side')):
            p = os.path.join(d, f'{act}_{k}_{v}.png')
            if os.path.exists(p):
                S.paste(Image.open(p).convert('RGB').resize((W, H)), (k * W, y + 14 + j * H))
S.save(out); print('SHEET', out, S.size)
