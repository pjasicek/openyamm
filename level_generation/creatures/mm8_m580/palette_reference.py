import numpy as np
from PIL import Image,ImageDraw
from process import ROOT,queue
names=['m580aa2','m580nc0','m580xa2']
out=Image.new('RGB',(1536,1650),(40,40,40));d=ImageDraw.Draw(out)
for i,n in enumerate(names):
 for j,p in enumerate([581,582,583]):
  im=queue.native(ROOT,n,p).resize((512,512),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,(40,40,40,255));bg.alpha_composite(im);out.paste(bg.convert('RGB'),(j*512,i*550+25));d.text((j*512+5,i*550+5),n+' palette '+str(p),fill='white')
out.save(ROOT/'references/native_palette_materials.png')
