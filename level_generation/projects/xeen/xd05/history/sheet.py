import sys, glob
from PIL import Image, ImageDraw
out=sys.argv[1]; fs=sorted(sum([glob.glob(a) for a in sys.argv[2:]],[]))
w,h=640,360
ims=[]
for f in fs:
    im=Image.open(f).convert('RGB').resize((w,h)); ImageDraw.Draw(im).text((6,6),f.split('/')[-1],fill=(255,255,0)); ims.append(im)
W=2;H=(len(ims)+1)//2
s=Image.new('RGB',(w*W,h*H))
for i,im in enumerate(ims): s.paste(im,((i%W)*w,(i//W)*h))
s.save(out,quality=85)
