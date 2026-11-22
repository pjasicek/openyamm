"""Contact sheet of pose_probe renders: rows = clips, columns = frames (view suffix given). Usage: sheet.py <dir> <view> <out>"""
import sys, os, re
from PIL import Image, ImageDraw
d, view, out = sys.argv[1:4]
files = sorted(f for f in os.listdir(d) if f.endswith(f'_{view}.png'))
clips = sorted({re.match(r'(.*)_\d_' + view, f).group(1) for f in files})
w, h = 160, 200
sheet = Image.new('RGB', (w * 4 + 110, h * len(clips)), 'white')
dr = ImageDraw.Draw(sheet)
for r, c in enumerate(clips):
    dr.text((4, r * h + 90), c, fill='black')
    for i in range(4):
        p = os.path.join(d, f'{c}_{i}_{view}.png')
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert('RGB').resize((w, h)), (110 + i * w, r * h))
sheet.save(out)
