"""Normalize generated olive stone to the selected native gray base; retain red eyes."""
from PIL import Image
import numpy as np
from pathlib import Path

def correct(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    stone=(g>=r*.80)&(g>b*1.08)&(g>.015)
    y=c@np.array([.2126,.7152,.0722]);c[stone]=y[stone,None]
    a[:,:,:3]=np.round(c*255).astype(np.uint8);return Image.fromarray(a)
if __name__=='__main__':
    root=Path(__file__).resolve().parent;correct(Image.open(root/'raw/standing.png')).save(root/'accepted_identity.png')
