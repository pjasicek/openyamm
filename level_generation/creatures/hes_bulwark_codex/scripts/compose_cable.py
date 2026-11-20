"""Small padded ceramic/bronze/resin atlas for the locally built coupling cables."""
import copy,json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];T=P/'textures'
y,x=np.mgrid[:256,:256];region=np.minimum(x//85,2)
base=np.array([[.17,.075,.20],[.77,.66,.45],[.68,.43,.14]])[region]*(.82+.12*np.cos(y[...,None]*2*np.pi/24)**4)
orm=np.array([[.3,.68,0],[.6,.58,0],[.85,.43,.85]])[region]
mask=np.zeros((256,256,4),np.uint8);mask[region==1,0]=255;mask[region==2,1]=255
classes=np.array([11,5,9],np.uint8)[region]
arrays={'basecolor':(base*255+.5).astype(np.uint8),'orm':(orm*255+.5).astype(np.uint8),'region_mask':mask,'material_classes':classes}
assert set(np.unique(classes))=={5,9,11} and np.all(mask.sum(2)<=255)
for name,a in arrays.items():
 path=T/f'bulwark_cable_{name}.png'
 if path.exists():assert np.array_equal(a,np.array(Image.open(path))),name
 Image.fromarray(a).save(path)
config=T/'bulwark_ramps.json';d=json.loads(config.read_text());body=next(m for m in d['materials'] if m['base']=='Bulwark_Armour')
cable={'base':'Bulwark_Cable','prefix':'Bulwark_Cable','mask':'bulwark_cable_region_mask.png','ramps':copy.deepcopy(body['ramps'])}
d['materials']=[m for m in d['materials'] if m['base']!='Bulwark_Cable']+[cable]
config.write_text(json.dumps(d,indent=2)+'\n')
print('Cable texture recipe matches all four delivered maps')
