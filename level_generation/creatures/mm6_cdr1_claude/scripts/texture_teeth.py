"""Bake a small enamel strip into unused head-atlas space and remove ivory bleed on the retained gum surface."""
import json,math,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';old=P/'work/before_teeth_v2/textures';N=2048
d=json.loads((P/'work/mouth_mesh.json').read_text());co=np.array(d['vertices']);labels=np.load(P/'work/mouth_components.npy');m=Image.new('L',(N,N));draw=ImageDraw.Draw(m)
for face,uv,material in zip(d['faces'],d['uv'],d['material']):
 c=co[face].mean(0)
 if material==1 and labels[face[0]] in [0,4] and c[1]<-1.385 and .822<c[2]<.940:
  draw.polygon([(u*N,(1-v)*N) for u,v in uv],fill=255)
mouth=ndimage.binary_dilation(np.array(m)>0,iterations=2);base=np.array(Image.open(old/'cdr1_head_basecolor_2k.png').convert('RGB'));hsv=np.array(Image.fromarray(base).convert('HSV'))/255;s=hsv[:,:,1];value=hsv[:,:,2]
white=mouth&(s<.50);red=mouth&(s>.52)&(base[:,:,0]>base[:,:,1]*1.4)
near=ndimage.distance_transform_edt(~red,return_distances=False,return_indices=True);repaired=base.copy();repaired[white]=base[tuple(near[:,white])]
tile=json.loads((P/'work/teeth_tile.json').read_text());x,y,w,h,pad=[tile[k] for k in ['x','y','width','height','padding']];tt=np.clip((h-pad-np.arange(h)) / (h-2*pad),0,1)[:,None,None];u=np.arange(w)[None,:,None]/w
root=np.array([.68,.60,.46]);tip=np.array([.92,.89,.78]);enamel=root+(tip-root)*np.sqrt(tt);grain=1+.009*np.sin(u*math.tau*9)+.005*np.sin(u*math.tau*23+tt*3);enamel=np.broadcast_to(enamel,(h,w,3))*grain
repaired[y:y+h,x:x+w]=np.uint8(np.clip(enamel,0,1)*255+.5)
allowed=white.copy();allowed[y:y+h,x:x+w]=True;assert np.array_equal(base[~allowed],repaired[~allowed]);Image.fromarray(repaired).save(T/'cdr1_head_basecolor_2k.png')
for suffix,mode,color in [('normal_2k','RGB',[128,128,255]),('metal_rough_2k','RGB',[100,100,0]),('region_mask','RGBA',[0,0,0,0]),('material_classes','L',4)]:
 a=np.array(Image.open(old/f'cdr1_head_{suffix}.png').convert(mode));a[y:y+h,x:x+w]=color
 if suffix=='normal_2k':a[white]=[128,128,255]
 if suffix=='metal_rough_2k':a[white]=[36,209,0]
 if suffix=='region_mask':a[white]=[255,0,0,0]
 if suffix=='material_classes':a[white]=1
 Image.fromarray(a).save(T/f'cdr1_head_{suffix}.png')
(P/'review/teeth_v2/texture.json').write_text(json.dumps({'atlas':'existing 2K head set','unused_tile':tile,'gum_bleed_texels_corrected':int(white.sum()),'new_paid_jobs':0,'teeth_region_mask':'all zero: enamel stays ivory in every tier','outside_target_basecolor_unchanged':True},indent=2)+'\n');print('ENAMEL',tile,'gum pixels',white.sum())
