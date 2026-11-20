"""Frozen, spatially independent native tonal-weight correction; enhanced material colors stay local."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
F=Path(__file__).resolve().parent
sys.path.insert(0,str(F.parent));import process

def grade(im,name):
    settings=json.loads((F/'tone_settings.json').read_text())
    a=np.array(im);v=a[:,:,:3]@np.array([.2126,.7152,.0722]);strength=settings['strength']
    target=(1-strength)*v+strength*np.interp(v,settings['input'],settings['target'])
    a[:,:,:3]=np.round(a[:,:,:3]*(target/np.maximum(v,1))[:,:,None]).clip(0,255).astype(np.uint8)
    result=process.fix(Image.fromarray(a),name)
    assert np.array_equal(np.asarray(result)[:,:,3],np.asarray(im)[:,:,3])
    return result
