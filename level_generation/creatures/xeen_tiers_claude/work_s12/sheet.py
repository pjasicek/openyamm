import sys, os
from PIL import Image, ImageDraw, ImageFont
out=sys.argv[1]; ids=sys.argv[2:]
names={}
for l in open('level_generation/creatures/xeen_tiers_claude/work_s12/all_tiers.tsv'):
    p=l.rstrip('\n').split('\t'); names[p[3]]=f"{p[3]} {p[2]} ({p[6]})"
W,H=384,252; cols=4
rows=(len(ids)+cols-1)//cols
sh=Image.new('RGB',(W*cols,(H+20)*rows),(20,20,20)); d=ImageDraw.Draw(sh)
for i,x in enumerate(ids):
    p=f'output/xeen_site_monsters/{x}.png'
    c,r=i%cols,i//cols
    if os.path.exists(p):
        im=Image.open(p).convert('RGB'); im.thumbnail((W,H)); sh.paste(im,(c*W,r*(H+20)+20))
    d.text((c*W+4,r*(H+20)+4),names.get(x,x),fill=(255,255,0))
sh.save(out)
