"""Reviewable material components on enhanced artwork; native masks are never transferred."""
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
from process import ROOT,save

def candidates(im):
    a=np.asarray(im);c=a[:,:,:3].astype(float)
    seed=(c[:,:,1]-c[:,:,0]>12)&(c[:,:,1]-c[:,:,2]>4)&(a[:,:,3]>200)
    lab,n=ndi.label(ndi.binary_closing(seed,iterations=2))
    parts=[]
    for obj in ndi.find_objects(lab):
        if obj is None:continue
        ids=lab[obj];valid=ids>0
        ident=int(ids[valid][0]);region=lab==ident;area=int((region&seed).sum())
        if area<24:continue
        ys,xs=np.where(region)
        parts.append((area,[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],region))
    parts.sort(key=lambda x:-x[0])
    return parts

def run():
    out={};(ROOT/'review/material_candidates').mkdir(exist_ok=True)
    for key,batch in json.loads((ROOT/'batches.json').read_text()).items():
        sheet=Image.new('RGB',(576*len(batch['frames']),610),(35,35,35));draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(batch['frames']):
            im=Image.open(ROOT/f'toned_2x/{name}.png').convert('RGBA');parts=candidates(im)
            bg=Image.new('RGBA',im.size,(35,35,35,255));bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(i*576,30));draw.text((i*576+5,5),name,fill='white')
            out[name]=[]
            for j,(area,box,reg) in enumerate(parts):
                out[name].append({'id':j,'area':area,'xyxy':box})
                x,y,x2,y2=box;draw.rectangle((i*576+x,y+30,i*576+x2,y2+30),outline=(255,70,50));draw.text((i*576+x2+1,y+25),str(j),fill=(255,255,0))
        sheet.save(ROOT/f'review/material_candidates/{key}.png')
    save(ROOT/'review/material_candidates.json',out)

if __name__=='__main__':run()
