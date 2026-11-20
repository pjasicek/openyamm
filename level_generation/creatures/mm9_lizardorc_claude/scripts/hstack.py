"""hstack.py out.png a.png b.png ...: images side by side, optional env SCALE"""
import sys,os
from PIL import Image
ims=[Image.open(x).convert('RGB') for x in sys.argv[2:]]; s=float(os.environ.get('SCALE',1))
w=sum(i.width for i in ims); h=max(i.height for i in ims)
o=Image.new('RGB',(w,h)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width
o.resize((int(w*s),int(h*s))).save(sys.argv[1])
