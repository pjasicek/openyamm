"""Deterministic enhanced-art masks and native palette contacts for refined poses."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import process,materials
ROOT=process.ROOT;D=ROOT/'detail_upgrade';config=materials.settings()
for folder in ['masks_2x','previews','review/variants','material_support_2x']:(D/folder).mkdir(parents=True,exist_ok=True)
keys=sys.argv[1:];jobs=json.loads((D/'jobs.json').read_text())['jobs']
for key in keys:
 names=jobs[key]['frames'] if key in jobs else ['m432sa0','m432aa0','m432ab0']
 sheet=Image.new('RGB',(256*len(names),1120),(35,35,35));draw=ImageDraw.Draw(sheet)
 for i,name in enumerate(names):
  path=D/'toned_2x'/f'{name}.png'
  if not path.exists():path=D/'review'/f'{name}_trial_2x.png'
  im=Image.open(path).convert('RGBA');mask=materials.masks(im,config)
  # Material support comes only from the refined RGB/alpha, never native mask pixels.
  a=np.asarray(im);rgb=a[:,:,:3].astype(float);red,green,blue=np.moveaxis(rgb,-1,0)
  seed=(mask>165)&(green-red>10)&(green>=blue-10)&(ndi.distance_transform_edt(a[:,:,3]>=250)>2)
  labels,count=ndi.label(seed);sizes=np.bincount(labels.ravel());sizes[0]=0;seed=sizes[labels]>=12
  support=np.clip((6-ndi.distance_transform_edt(~seed))/2,0,1) if seed.any() else np.zeros(seed.shape)
  Image.fromarray(np.round(support*255).astype(np.uint8)).save(D/'material_support_2x'/f'{name}.png')
  mask=np.round(mask*support).astype(np.uint8)
  protection=json.loads((D/'mask_protection.json').read_text())['polygons'] if (D/'mask_protection.json').exists() else {}
  if name in protection:
   keep=Image.new('L',im.size,255);brush=ImageDraw.Draw(keep)
   for polygon in protection[name]:brush.polygon([tuple(p) for p in polygon],fill=0)
   mask=np.minimum(mask,np.array(keep))
  Image.fromarray(mask).save(D/'masks_2x'/f'{name}.png');pics=[]
  for pal in materials.PALETTES:
   v=materials.recolor(im,mask,pal,config);assert np.array_equal(np.asarray(v)[:,:,3],np.asarray(im)[:,:,3]);assert pal!=433 or np.array_equal(np.asarray(v),np.asarray(im));v.save(D/'previews'/f'{name}_{pal}.png');pics.append(v)
  a=np.array(im);m=mask/255;a[:,:,:3]=np.round(a[:,:,:3]*(1-.65*m[:,:,None])+np.array([255,70,30])*.65*m[:,:,None]).astype(np.uint8);pics.append(Image.fromarray(a))
  for row,pic in enumerate(pics):
   bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);sheet.paste(bg.resize((256,256),Image.Resampling.LANCZOS).convert('RGB'),(i*256,row*280+24));draw.text((i*256+4,row*280+4),name+' '+str([*materials.PALETTES,'mask'][row]),fill='white')
 sheet.save(D/'review/variants'/f'{key}.png');print(key,'palette contacts ready',flush=True)
config['enhanced_material_support']={'seed':'enhanced mask > 165/255, G-R > 10, G >= B-10, opaque interior distance > 2 pixels; connected seed size >= 12 pixels','coverage':'full within 4 pixels of enhanced seeds, soft falloff to zero at 6 pixels','reason':'Prevent demonstrated thin steel-highlight recoloring; keep enhanced green sleeve bands and teal disks. Masks only, no alpha or RGB transfer.'}
process.save(D/'material_settings.json',config)
