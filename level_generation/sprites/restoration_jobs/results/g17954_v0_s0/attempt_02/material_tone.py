from pathlib import Path
import json
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
k=next(iter(json.loads((p/'checks.json').read_text())["frames"]))
a=np.array(Image.open(p/f"{k}.before_tone_095.png").convert("RGBA"))
n=np.array(Image.open(p.parents[2]/"native"/f"{k}.png").convert("RGBA"))
def foliage(rgb):
    return np.clip((rgb[:,:,1]-rgb[:,:,0]+2)/12,0,1)
rgb=a[:,:,:3].astype(float);nrgb=n[:,:,:3].astype(float)
w=foliage(rgb);nw=foliage(nrgb)
graded=[];report={}
for name,sel,nsel in [("foliage",w>.9,nw>.9),("bark",w<.1,nw<.1)]:
    sample=rgb[sel & (a[:,:,3]>=192)]/255
    target=nrgb[nsel & (n[:,:,3]>=192)].mean(axis=0)/255
    gamma=[]
    for c in range(3):
        lo,hi=.1,5.
        for _ in range(40):
            mid=(lo+hi)/2
            if (sample[:,c]**mid).mean()>target[c]:lo=mid
            else:hi=mid
        gamma.append((lo+hi)/2)
    graded.append((rgb/255)**np.array(gamma)*255)
    report[name]={"gamma":gamma,"native_mean_rgb":(target*255).tolist()}
a[:,:,:3]=np.clip(np.rint(graded[0]*w[:,:,None]+graded[1]*(1-w[:,:,None])),0,255).astype(np.uint8)
Image.fromarray(a).save(p/f"{k}.png")
report["alpha"]="unchanged"
(p/"material_tone.json").write_text(json.dumps(report,indent=2)+"\n")
