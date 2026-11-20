from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import map_coordinates, binary_closing,binary_fill_holes,gaussian_filter,distance_transform_edt
P=Path('level_generation/terrain/mm8');V=P/'roads/v13';(V/'trials').mkdir(exist_ok=True)
donor=np.asarray(Image.open(P/'roads/v7/runtime/drsrew.png').convert('RGB'),float).transpose(1,0,2)
# Use the actual accepted NS road's complete strip, including stone bevel and grout.
coverage=(donor[:,:,1]>.77*donor[:,:,0])&(donor[:,:,2]>.58*donor[:,:,0])
coverage=binary_fill_holes(binary_closing(np.pad(coverage,8,mode='wrap'),iterations=4)[8:-8,8:-8])
coverage=gaussian_filter(coverage.astype(float),.5)
y,x=np.indices((256,256));sheet=Image.new('RGB',(1024,1024));draw=ImageDraw.Draw(sheet)
for trial,speed in enumerate([.5,1]):
 tiles={}
 for suffix in ['ne1','ne2']:
  u=x-y+(256 if suffix=='ne1' else 0)
  v=(x+y)*speed+(128 if suffix=='ne1' and speed==.5 else 0)
  rgb=np.stack([map_coordinates(donor[:,:,c],[v%256,np.clip(u,0,255)],order=1,mode='grid-wrap') for c in range(3)],2)
  a=map_coordinates(coverage,[v%256,np.clip(u,0,255)],order=1,mode='grid-wrap')*(u>=0)*(u<=255)
  dirt=np.asarray(Image.open(P/'masters/v1/runtime/dirt.png'),float);dist=distance_transform_edt(a<.5)
  shade=.2*np.exp(-dist/1.4)*(1-a)
  out=rgb*a[:,:,None]+dirt*(1-shade[:,:,None])*(1-a[:,:,None])
  im=Image.fromarray(np.uint8(np.clip(out,0,255)));im.save(V/'trials'/f'ew{trial}_drsr{suffix}.png');tiles[suffix]=im
 for row in range(3):
  for col in range(2):
   n='ne2' if col==row%2 else 'ne1'
  # Stacked 2x2 path: NE2 above NE1, NE1 to its right.
 sheet.paste(tiles['ne2'],(trial*512,0));sheet.paste(tiles['ne1'],(trial*512+256,0));sheet.paste(tiles['ne2'],(trial*512+256,256))
 sheet.paste(tiles['ne1'],(trial*512,512));sheet.paste(tiles['ne2'],(trial*512,768));sheet.paste(tiles['ne1'],(trial*512+256,768))
sheet.save(V/'ew_trials.png')
