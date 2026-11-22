#!/usr/bin/env python3
"""Contact sheet of native textures by name: sheet.py out.png name1 name2 ..."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys, glob, os
from PIL import Image, ImageDraw
R=_REPO_ROOT + '/assets_source/worlds'
out=sys.argv[1]; names=sys.argv[2:]
cell=160; cols=8
rows=(len(names)+cols-1)//cols
sheet=Image.new('RGB',(cols*cell,rows*(cell+14)),(30,30,30))
d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
    hits=[p for pat in (R+'/*/textures_x4/*',R+'/*/textures_x2/*',R+'/*/textures/*',_REPO_ROOT + '/assets_source/textures/native_mm6_mm8/*/textures/*') for p in sorted(glob.glob(pat)) if os.path.splitext(os.path.basename(p))[0].lower()==n.lower()]
    x=(i%cols)*cell; y=(i//cols)*(cell+14)
    if hits:
        im=Image.open(hits[0]).convert('RGB'); w,h=im.size; s=min(cell/w,cell/h)
        im=im.resize((max(1,int(w*s)),max(1,int(h*s))))
        sheet.paste(im,(x,y))
        d.text((x+2,y+cell),f"{n} {w}x{h}",fill=(255,255,0))
    else:
        d.text((x+2,y+cell),f"{n} ?",fill=(255,80,80))
sheet.save(out)
