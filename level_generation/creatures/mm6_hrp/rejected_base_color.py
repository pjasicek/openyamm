"""Restore selected native base color on existing enhanced art; raw output retained."""
from pathlib import Path
from PIL import Image
import numpy as np

def correct(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    w=np.clip((r/np.maximum(g,.015)-2.1)/1.2,0,1)*np.clip((g-b+.03)/.05,0,1)
    # Strong red plumage only; preserve brown feathers, golden talons and magenta key.
    target=np.stack([g*.8,r*.72,b*.8],2)
    c=c*(1-w[:,:,None])+target*w[:,:,None];a[:,:,:3]=np.round(np.clip(c,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
if __name__=='__main__':
    root=Path(__file__).resolve().parent;correct(Image.open(root/'raw/standing.png')).save(root/'accepted_identity.png')
