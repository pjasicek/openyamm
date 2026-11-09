"""Normalize generated blue tabard/eyes to selected native charcoal/green base."""
from PIL import Image
import numpy as np
from pathlib import Path

def correct(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    blue=np.clip((b-np.maximum(r,g)-.015)/.055,0,1)
    eye=blue*np.clip((b-.40)/.25,0,1)*np.clip((g-r-.08)/.15,0,1)
    cloth=blue*(1-eye);y=c@np.array([.2126,.7152,.0722]);target=y[:,:,None]*np.array([.98,.92,1.12])
    c=c*(1-cloth[:,:,None])+target*cloth[:,:,None]
    target=np.stack([g,b,r],2);c=c*(1-eye[:,:,None])+target*eye[:,:,None]
    a[:,:,:3]=np.round(np.clip(c,0,1)*255).astype(np.uint8);return Image.fromarray(a)
if __name__=='__main__':
    root=Path(__file__).resolve().parent;correct(Image.open(root/'raw/standing.png')).save(root/'accepted_identity.png')
