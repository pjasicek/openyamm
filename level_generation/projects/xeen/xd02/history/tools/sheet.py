# Contact sheet: sheet.py <out.jpg> <cols> <cell_width> <png...>; each cell labelled with its file name.
import sys
from PIL import Image, ImageDraw
out, cols, cw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = []
for f in files:
    im = Image.open(f).convert('RGB')
    h = int(im.height * cw / im.width)
    ims.append((f.split('/')[-1], im.resize((cw, h))))
ch = max(i.height for _, i in ims)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cw, rows * (ch + 18)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for k, (name, im) in enumerate(ims):
    x, y = (k % cols) * cw, (k // cols) * (ch + 18)
    sheet.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), name, fill=(255, 255, 0))
sheet.save(out, quality=82)
