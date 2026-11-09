import sys
from PIL import Image
out=sys.argv[1]; cols=int(sys.argv[2]); fs=sys.argv[3:]
ims=[Image.open(f).convert('RGB') for f in fs]; w,h=ims[0].size
rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(cols*w,rows*h))
for i,im in enumerate(ims): s.paste(im,((i%cols)*w,(i//cols)*h))
s.save(out)
