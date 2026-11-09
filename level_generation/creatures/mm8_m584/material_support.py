"""Enhanced-color material seeds with reviewable local corrections, no native mask transfer."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from process import ROOT,save

def support(im,name,seed_green=45,minimum_area=30):
    a=np.asarray(im);c=a[:,:,:3].astype(float)
    green=c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2])
    seed=(green>seed_green)&(a[:,:,3]>200)
    lab,n=ndi.label(ndi.binary_closing(seed,iterations=1));sizes=ndi.sum(seed,lab,range(n+1));sizes[0]=0
    selected=np.isin(lab,np.where(sizes>=minimum_area)[0]);selected&=lab>0
    distance=ndi.distance_transform_edt(~selected) if selected.any() else np.full(seed.shape,1000.)
    allowed=np.clip((10-distance)/4,0,1)
    path=ROOT/'material_region_overrides.json'
    edits=json.loads(path.read_text()).get(name,{}) if path.exists() else {}
    for field,value in [('include',1),('exclude',0)]:
        for x,y,x2,y2 in edits.get(field,[]):allowed[y:y2,x:x2]=value
    return allowed

def protect(im,name):
    a=np.array(im);c=a[:,:,:3].astype(float);allowed=support(im,name)
    green=c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2])
    # Remove demonstrated green cast on protected feathers and talons; retain luminance and fine RGB variation.
    excess=np.maximum(0,green-2)*(1-allowed)
    c[:,:,1]-=excess
    c+=excess[:,:,None]*.7152
    a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8);a[a[:,:,3]==0]=0
    return Image.fromarray(a)

def review():
    (ROOT/'review/material_support').mkdir(exist_ok=True)
    for key,batch in json.loads((ROOT/'batches.json').read_text()).items():
        sheet=Image.new('RGB',(384*len(batch['frames']),440),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(batch['frames']):
            im=Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA');a=np.array(im);mask=support(im,name)
            a[:,:,:3]=np.round(a[:,:,:3]*(1-.7*mask[:,:,None])+np.array([255,30,0])*.7*mask[:,:,None]).astype(np.uint8)
            bg=Image.new('RGBA',im.size,(35,35,35,255));bg.alpha_composite(Image.fromarray(a));sheet.paste(bg.resize((384,384)).convert('RGB'),(i*384,30));draw.text((i*384+4,5),name,fill='white')
        sheet.save(ROOT/f'review/material_support/{key}.png')
    print('Material support review prepared')

if __name__=='__main__':review()
