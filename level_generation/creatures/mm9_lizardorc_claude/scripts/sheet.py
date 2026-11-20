"""sheet.py out.png cols size name1 name2 ...: review/shots/<name>.png into a grid, centre-cropped square."""
import sys
from PIL import Image, ImageDraw
out,cols,S=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); ns=sys.argv[4:]
rows=(len(ns)+cols-1)//cols; o=Image.new('RGB',(cols*S,rows*S),(40,40,40))
for i,n in enumerate(ns):
    im=Image.open(f'review/shots/{n}.png').convert('RGB'); w,h=im.size; im=im.crop(((w-h)//2,0,(w+h)//2,h)).resize((S,S)); ImageDraw.Draw(im).text((3,3),n,fill=(255,255,0)); o.paste(im,((i%cols)*S,(i//cols)*S))
o.save(out)
