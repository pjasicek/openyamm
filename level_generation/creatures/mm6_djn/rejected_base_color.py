"""Restore selected native base color on existing enhanced art; raw output retained."""
from pathlib import Path
from PIL import Image
import numpy as np

def correct(image):
    a=np.array(image);c=a[:,:,:3].astype(float)/255;r,g,b=c.transpose(2,0,1)
    w=np.clip((np.minimum(r,b)-g-.025)/.08,0,1)*np.clip((g-.015)/.04,0,1)
    # Purple skin to native blue, preserving unsaturated vortex ridges and key.
    y=c@np.array([.2126,.7152,.0722]);target=y[:,:,None]*np.array([.48,1.06,1.65])
    c=c*(1-w[:,:,None])+target*w[:,:,None];a[:,:,:3]=np.round(np.clip(c,0,1)*255).astype(np.uint8)
    return Image.fromarray(a)
if __name__=='__main__':
    root=Path(__file__).resolve().parent;correct(Image.open(root/'raw/standing.png')).save(root/'accepted_identity.png')
