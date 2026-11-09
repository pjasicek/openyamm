import sys
from PIL import Image, ImageDraw
S, label, frames, views = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')], sys.argv[4].split(',')
w, h = 300, 323; out = Image.new('RGB', (w * len(frames), h * len(views)), 'gray'); d = ImageDraw.Draw(out)
for j, v in enumerate(views):
    for i, f in enumerate(frames):
        im = Image.open(f'{S}/{label}_{v}_{f:02d}.png').convert('RGB').resize((w, h)); out.paste(im, (i * w, j * h)); d.text((i * w + 4, j * h + 4), f'{v} f{f} {f/48:.2f}s', fill='yellow')
out.save(f'{S}/{label}_sheet.png'); print(f'{S}/{label}_sheet.png')
