"""Bake generated art through the measured surface projector and prop UV layout."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
src=Image.open(P/'references_feedback_v2/poseidon_front.png').convert('RGB');atlas=Image.new('RGB',(1024,1024))
atlas.paste(src.crop((230,0,656,540)).resize((640,1024),Image.Resampling.LANCZOS),(0,0));atlas.paste(src.crop((403,515,483,1745)).resize((358,1024),Image.Resampling.LANCZOS),(666,0));atlas.save(T/'wel_trident_basecolor.png')
a=np.asarray(atlas,float)/255;purple=(a[...,2]>a[...,0]*1.15)&(a[...,2]>a[...,1]*1.3);mr=np.tile([.88,.32,.82],(N,N,1));mr[purple]=[.45,.43,.12];save(mr,T/'wel_trident_metal_rough.png');Image.new('RGBA',(N,N),(0,0,0,0)).save(T/'wel_trident_region_mask.png')
# Geometry-guided face projector: generated facial landmarks are registered to the sculpt.
d=np.load(P/'work/uvraster_head.npz');pos=d['pos'];part=d['piece'];cov=part>=0;x,y,z=np.moveaxis(pos,-1,0)
src=np.asarray(Image.open(P/'references_feedback_v2/face_projection.png').convert('RGB'),float)/255
u=.5+(x+.01)/.36;v=.5+(1.93-z)/.36
v=np.interp(v,[0,.45,.548,.649,.710,.83,1],[0,.45,.547,.662,.750,.86,1])
sample=np.stack([ndimage.map_coordinates(src[...,c],[v*src.shape[0]-.5,u*src.shape[1]-.5],order=1,mode='nearest') for c in range(3)],-1)
def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
w=smooth((.112-abs(x+.01))/.035)*smooth((-y-.015)/.035)*smooth((z-1.785)/.045)*smooth((2.005-z)/.045)*(part==0)
base=np.asarray(Image.open(P/'review/revisions/water_v1/textures'/'wel_head_basecolor_1k.png').convert('RGB'),float)/255
cheek=(w>.95)&(abs(x+.01)>.05)&(z>1.85)&(z<1.90);gain=np.clip(np.median(base[cheek],axis=0)/np.median(sample[cheek],axis=0),.8,1.2);sample*=gain
base=base*(1-w[...,None])+sample*w[...,None]
idx=tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True));save(base[idx],T/'wel_head_basecolor_1k.png')
normal=np.asarray(Image.open(P/'review/revisions/water_v1/textures'/'wel_head_normal_1k.png').convert('RGB'),float)/255
# The original normal atlas repeats the misplaced nose and mouth; keep the sculpt in this registered face region.
normal=normal*(1-w[...,None])+np.array([.5,.5,1])*w[...,None];save(normal[idx],T/'wel_head_normal_1k.png')
mask=np.asarray(Image.open(P/'review/revisions/water_v1/textures'/'wel_head_region_mask.png').convert('RGBA'),float)/255
hair=smooth((1.895-z)/.03)*smooth((sample[...,0]/np.maximum(sample[...,1],.01)-1.07)/.12)*smooth((sample[...,1]/np.maximum(sample[...,2],.01)-1.12)/.16)
new=np.zeros_like(mask);new[...,0]=1-hair;new[...,3]=hair;mask=mask*(1-w[...,None])+new*w[...,None];save(mask[idx],T/'wel_head_region_mask.png')
(P/'review/feedback_v2/face_projection.json').write_text(json.dumps({'method':'Registered orthographic texture projection into existing head UVs','single_surface':True,'head_material_faces':6912,'cheek_color_gain':gain.tolist(),'source':'references_feedback_v2/face_projection.png'},indent=2))
