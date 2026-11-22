import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, glob, os
from PIL import Image, ImageDraw
names = sys.argv[2:]
out = sys.argv[1]
cells = []
for n in names:
    hits = []
    R=_REPO_ROOT + '/'
    for w in ('mm6','mm7','mm8','mm9','xeen'):
        for pat in (f'assets_source/worlds/{w}/textures_x4/{n}.png', f'assets_source/textures/native_mm6_mm8/{w}/textures/{n}.bmp', f'assets_source/worlds/{w}/textures/{n}.bmp', f'tools/upscaling/out_prod_bmodel_{w}/{n}.png'):
            hits += glob.glob(R+pat)
    if not hits:
        print('missing', n); continue
    im = Image.open(hits[0]).convert('RGB')
    w,h = im.size
    s = 192/max(w,h)
    im = im.resize((max(1,int(w*s)), max(1,int(h*s))))
    c = Image.new('RGB',(200,214),(30,30,30))
    c.paste(im,(4,4))
    ImageDraw.Draw(c).text((4,200), f'{n} {w}x{h}', fill=(255,255,0))
    cells.append(c)
cols = 6
rows = (len(cells)+cols-1)//cols
sheet = Image.new('RGB',(cols*200, rows*214),(0,0,0))
for i,c in enumerate(cells):
    sheet.paste(c,((i%cols)*200,(i//cols)*214))
sheet.save(out)
