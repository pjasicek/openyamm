import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; rows = sys.argv[2:]
# each row arg: label=prefix ; views front,q,side,back,qleft
views = ['front', 'q', 'qleft', 'side', 'back']
cell = 300
S = Image.new('RGB', (cell * len(views) + 120, cell * len(rows)), (40, 40, 40))
d = ImageDraw.Draw(S)
for r, arg in enumerate(rows):
    label, prefix = arg.split('=')
    d.text((5, r * cell + cell // 2), label, fill=(255, 255, 255))
    for c, v in enumerate(views):
        try:
            im = Image.open(f'{prefix}_{v}.png').convert('RGB').resize((cell, cell))
            S.paste(im, (120 + c * cell, r * cell))
        except FileNotFoundError:
            pass
S.save(out)
