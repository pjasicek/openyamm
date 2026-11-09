"""Contact sheet of cropped x2 sprites on grey: contact.py out.png scale name1 name2 ..."""
import sys
from PIL import Image, ImageDraw
X2 = 'assets_dev/engine/decorations_x2/'
out, scale, names = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
ims = []
for n in names:
    im = Image.open(X2 + n + '.png').convert('RGBA')
    bb = im.split()[-1].getbbox()
    im = im.crop(bb)
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.NEAREST)
    ims.append((n, im))
W = sum(i.width for _, i in ims) + 20 * (len(ims) + 1)
H = max(i.height for _, i in ims) + 40
sheet = Image.new('RGB', (W, H), (110, 110, 110))
d = ImageDraw.Draw(sheet)
x = 20
for n, im in ims:
    sheet.paste(im, (x, H - 10 - im.height), im)
    d.text((x, 4), n, fill=(255, 255, 255))
    x += im.width + 20
sheet.save(out)
