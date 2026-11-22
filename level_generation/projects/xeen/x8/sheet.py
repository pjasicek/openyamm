import sys
from pathlib import Path
from PIL import Image
d=Path(sys.argv[1]); out=sys.argv[2]; files=sorted(d.glob('*.png'))
sel=files[int(sys.argv[3]):int(sys.argv[4])] if len(sys.argv)>4 else files
W=Image.new('RGB',(1280,360*((len(sel)+1)//2)))
for k,f in enumerate(sel): W.paste(Image.open(f).convert('RGB').resize((640,360)),((k%2)*640,(k//2)*360))
W.save(out)
