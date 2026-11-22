import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, os
from PIL import Image, ImageDraw
R=_REPO_ROOT + '/level_generation/textures_x4/masters'
names=sys.argv[2:]; out=sys.argv[1]
cells=[]
for n in names:
    p=None
    for w in ('mm8','mm7','mm6'):
        q=f'{R}/{w}/{n}.png'
        if os.path.exists(q): p=q; break
    if not p:
        q=next((p for p in __import__('glob').glob(f'{_REPO_ROOT}/level_generation/**/finished/{n}.png', recursive=True)), '')
        if os.path.exists(q): p=q
    if not p: print('missing',n); continue
    im=Image.open(p).convert('RGB'); im.thumbnail((256,256))
    c=Image.new('RGB',(260,280),(40,40,40)); c.paste(im,(2,2)); ImageDraw.Draw(c).text((4,262),f'{n} {Image.open(p).size}',fill=(255,255,255)); cells.append(c)
cols=6; rows=(len(cells)+cols-1)//cols
S=Image.new('RGB',(cols*260,rows*280),(0,0,0))
for i,c in enumerate(cells): S.paste(c,((i%cols)*260,(i//cols)*280))
S.save(out)
