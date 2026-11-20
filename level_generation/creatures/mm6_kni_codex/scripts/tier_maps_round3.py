"""Bake engine region ramps only for comparative PBR renders and the shared viewer."""
import sys,json,numpy as np
from PIL import Image
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';T=P/'textures/round3';sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
def ramp(colors,t):
 c=np.array(colors,np.float32);x=np.clip(t,0,1)*(len(c)-1);i=np.minimum(x.astype(int),len(c)-2);f=(x-i)[...,None];return c[i]*(1-f)+c[i+1]*f
def build():
 d,_=read_glb(W/'high_body.glb')
 for variant in ['high','low']:
  base=W/'high_basecolor.png'if variant=='high'else T/'knight_basecolor.png';mask=W/'high_region_mask.png'if variant=='high'else T/'knight_region_mask.png'
  im=Image.open(base).convert('RGB');rgb=lin(np.asarray(im,np.float32)/255);lum=rgb@np.array([.2126,.7152,.0722]);ma=np.stack([np.asarray(c.resize(im.size,Image.Resampling.BILINEAR),np.float32)/255 for c in Image.open(mask).convert('RGBA').split()],-1)
  for i,tier in enumerate('abc'):
   out=rgb.copy();entry=d['materials'][i]['extras']['openyamm_region_ramps']
   for j,reg in enumerate(entry):
    lo,hi=reg['range'];out=out*(1-ma[...,j:j+1])+ramp(reg['colors'],(lum-lo)/(hi-lo))*ma[...,j:j+1]
   Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype(np.uint8)).save(W/f'{variant}_tier_{tier}.png')
if __name__=='__main__':build()
