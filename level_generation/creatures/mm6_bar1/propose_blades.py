"""Propose enhanced blade axes for explicit visual review before mask exclusion."""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent
proposals = {}
paths = sorted((ROOT / 'aligned_2x').glob('*.png'))
sheet = Image.new('RGB', (8 * 240, ((len(paths)+7)//8)*340), '#353535')
for i,path in enumerate(paths):
    im=Image.open(path).convert('RGBA'); a=np.array(im); rgb=a[:,:,:3].astype(float)
    r,g,b=rgb.transpose(2,0,1)
    pale = ((a[:,:,3]>128)&(b>r)&(g>r)&(g>85)&((b-r)<80)&((g-r)<65)).astype(np.uint8)*255
    lines=cv2.HoughLinesP(pale,1,np.pi/720,25,minLineLength=30,maxLineGap=8)
    line=None
    if lines is not None:
        line=max(lines[:,0,:].tolist(),key=lambda l:(l[2]-l[0])**2+(l[3]-l[1])**2)
        proposals[path.stem]=line
    out=Image.new('RGBA',im.size,'#353535');out.alpha_composite(im)
    if line: ImageDraw.Draw(out).line(tuple(line),fill='#ff2020',width=3)
    out.thumbnail((234,310))
    sheet.paste(out,(i%8*240+(240-out.width)//2,i//8*340+25))
    ImageDraw.Draw(sheet).text((i%8*240+5,i//8*340+5),path.stem,fill='white')
(ROOT/'blade_axes_proposed.json').write_text(json.dumps(proposals,indent=2)+'\n')
sheet.save(ROOT/'review/blade_axes_proposed.png')
