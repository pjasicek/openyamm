import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as nd
P=Path(__file__).resolve().parents[1]
for level in range(4):
 folder=P/f'textures/lod{level}';backup=P/f'review/round1/before/textures_lod{level}'
 if not backup.exists():shutil.copytree(folder,backup)
 data=np.load(P/f'work/round1_mep_lod{level}.npz');piece=data['piece'];pos=data['pos'];occupied=piece>=0
 base=np.array(Image.open(backup/'mep_basecolor.png').convert('RGB'))/255;old=np.array(Image.open(backup/'mep_region_mask.png').convert('RGBA'))/255
 mask=np.zeros((*piece.shape,4));mask[:,:,2]=1;mask[piece==1]=[0,1,0,0];red=np.isin(piece,[7,8])|(piece>=14);mask[red]=[1,0,0,0];mask[np.isin(piece,[2,3,5,6,10,11])]=[0,0,0,1]
 coat=np.isin(piece,[0,9]);lum=base@np.array([.2126,.7152,.0722]);bad=coat&((old[:,:,0]>.08)|((base[:,:,0]-base[:,:,1])>.08)|((lum<.40)&(pos[:,:,1]<-.08)&(pos[:,:,2]<1.39)))
 good=coat&~bad&(lum>.50);assert good.any();_,near=nd.distance_transform_edt(~good,return_indices=True);base[bad]=base[near[0][bad],near[1][bad]]
 # The modelled sash and buttons own their complete colour; projection rays had borrowed adjacent coat texels.
 shade=np.clip(lum,.30,.65);base[red]=np.repeat(shade[red,None],3,axis=1)
 normal=np.array(Image.open(backup/'mep_normal.png').convert('RGB'));normal[bad]=[128,128,255]
 _,near=nd.distance_transform_edt(~occupied,return_indices=True)
 for arr,name in [(base,'mep_basecolor.png'),(mask,'mep_region_mask.png')]:
  arr=arr[near[0],near[1]];Image.fromarray(np.uint8(np.clip(arr*255+.5,0,255))).save(folder/name)
 normal=normal[near[0],near[1]];Image.fromarray(normal).save(folder/'mep_normal.png')
 print('SEMANTIC_TEXTURE',level,'coat cleaned',int(bad.sum()),'red',int(red.sum()),flush=True)
