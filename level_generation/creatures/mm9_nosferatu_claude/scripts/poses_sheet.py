import glob,os,sys
from PIL import Image, ImageDraw
d=sys.argv[1]; out=sys.argv[2]
names=sorted({os.path.basename(f).rsplit('_',1)[0] for f in glob.glob(d+'/*.png')})
fr=sorted({os.path.basename(f).rsplit('_',1)[1] for f in glob.glob(d+'/*.png')})
s=int(sys.argv[3]) if len(sys.argv)>3 else 220
im=Image.new('RGB',(s*len(fr),s*len(names)))
dr=ImageDraw.Draw(im)
for r,n in enumerate(names):
    for c,f in enumerate(fr):
        p=f'{d}/{n}_{f}'
        if os.path.exists(p): im.paste(Image.open(p).convert('RGB').resize((s,s)),(c*s,r*s))
    dr.text((4,r*s+2),n,fill=(255,255,0))
im.save(out)
