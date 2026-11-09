"""Authored UV material atlas: forged steel, scored wood, leather and native shield panels."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
P=Path(__file__).resolve().parents[1]; T=P/'textures'; N=1024
rng=np.random.default_rng(535)
y,x=np.mgrid[:N,:N]
fine=rng.normal(0,1,(N,N)); cloud=gaussian_filter(fine,12); cloud/=cloud.std()
noise=gaussian_filter(fine,1.1); noise/=noise.std()
base=np.zeros((N,N,3)); height=np.zeros((N,N)); rough=np.full((N,N),.67); spec=np.full((N,N),.4); mask=np.zeros((N,N,4))
tiles={'shield':[16,16,496,1008],'steel':[520,8,760,248],'edge':[776,8,1016,248],
       'dark':[520,264,760,504],'wood':[776,264,1016,504],'leather':[520,520,760,760],
       'brass':[776,520,1016,760],'back':[520,776,760,1016],'paint':[776,776,1016,1016]}
# Full tile gutters use the same material; no tiny repeated colour swatches.
for name,(x0,y0,x1,y1) in tiles.items():
 sl=np.s_[y0:y1,x0:x1]; X=x[sl]-x0;Y=y[sl]-y0;grain=noise[sl];mottle=cloud[sl]
 steel=name in ['shield','steel','edge']; h=.08*grain+.12*mottle
 if steel:
  v={'shield':.56,'steel':.51,'edge':.64}[name]+.016*grain+.022*mottle
  base[sl]=v[:,:,None];mask[sl+(2,)]=1;rough[sl]=.62+.03*grain;spec[sl]=.42 if name!='edge' else .52
 elif name=='dark':base[sl]=np.array([.24,.25,.255])[None,None,:]*(1+.07*grain[:,:,None]+.06*mottle[:,:,None]);rough[sl]=.67
 elif name in ['wood','back']:
  stripes=np.sin(X*.32+np.sin(Y*.045)*.7)+.35*np.sin(X*1.5+Y*.012)
  v=1+.08*stripes+.025*grain+.06*mottle;base[sl]=np.array([.26,.15,.074])*v[:,:,None];h+=stripes*.08;rough[sl]=.81;spec[sl]=.15
 elif name=='leather':
  seam=np.exp(-((Y%38-3)/1.7)**2);v=1+.035*grain+.08*mottle-.27*seam
  base[sl]=np.array([.19,.105,.06])*v[:,:,None];h-=seam*.4;rough[sl]=.78;spec[sl]=.18
 elif name=='brass':base[sl]=np.array([.39,.29,.12])*(1+.045*grain[:,:,None]+.055*mottle[:,:,None]);rough[sl]=.57;spec[sl]=.48
 else:base[sl]=(.47+.018*grain+.03*mottle)[:,:,None];mask[sl+(0,)]=1;rough[sl]=.75;spec[sl]=.18
 height[sl]=h
# The native shield is predominantly steel; two coloured side inlays surround a steel central diamond.
x0,y0,x1,y1=tiles['shield']
def shield_uv(a,z):return (x0+(a+.20)/.40*(x1-x0),y1-(z+.42)/.82*(y1-y0))
paint=Image.new('L',(N,N));draw=ImageDraw.Draw(paint)
for side in [-1,1]:
 points=[(.092,.333),(.155,.16),(.113,-.339),(.076,-.351),(.105,-.042),(.04,.325)]
 draw.polygon([shield_uv(a*side,z) for a,z in points],fill=255)
pigment=np.asarray(paint)>0;base[pigment]=(.48+.023*noise[pigment]+.025*cloud[pigment])[:,None]
mask[pigment]=[1,0,0,0];rough[pigment]=.78;spec[pigment]=.22
# Fine engraved perimeter and scratches live in the maps; raised rim/boss/studs live in geometry.
scratches=Image.new('L',(N,N));dr=ImageDraw.Draw(scratches)
for _ in range(1250):
 a=int(rng.integers(16,N-16));b=int(rng.integers(16,N-16));length=int(rng.integers(3,30))
 dr.line([(a,b),(a+int(rng.integers(-5,6)),b+length)],fill=int(rng.integers(15,70)),width=1)
sc=np.asarray(scratches)/255; height-=sc*.7;base*=1-sc[:,:,None]*.28
# Small wear flecks expose grey metal within the pigment, rather than adding geometry.
wear=pigment&(fine>2.2);base[wear]=.52;mask[wear]=[0,0,1,0]
gy,gx=np.gradient(gaussian_filter(height,.6));normal=np.stack([-gx*1.1,gy*1.1,np.ones((N,N))],-1);normal/=np.linalg.norm(normal,axis=2)[:,:,None]
for name,data in [('basecolor',base),('normal',normal*.5+.5),('metal_rough',np.stack([spec,rough,np.zeros((N,N))],-1))]:
 Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5)).save(T/f'figc_gear_{name}_1k.png')
Image.fromarray(np.uint8(mask*255)).save(T/'figc_gear_region_mask.png')
cfg=json.loads((T/'figc_ramps.json').read_text());template=cfg['materials'][0];ramps={}
# Native-inspired inset colours remain tiered while every steel ramp uses the same dull grey response.
colors={'figc_a':np.array([.40,.25,.075]),'figc_b':np.array([.35,.095,.12]),'figc_c':np.array([.45,.15,.075])}
lin=lambda a:np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
for k in cfg['variants']:
 rr=json.loads(json.dumps(template['ramps'][k]));rr[0]={'range':[.07,.35],'colors':[(lin(colors[k])*(.55+1.05*j/15)).tolist() for j in range(16)]};ramps[k]=rr
cfg['materials']=[m for m in cfg['materials'] if m['base']!='FighterChainGear_A']
cfg['materials'].append({'base':'FighterChainGear_A','prefix':'FighterChainGear','mask':'figc_gear_region_mask.png','regions':template['regions'],'palettes':template['palettes'],'ramps':ramps})
(T/'figc_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(T/'figc_gear_tiles.json').write_text(json.dumps(tiles,indent=2)+'\n')
assert np.isfinite(base).all() and np.isfinite(normal).all()
assert all(np.allclose(ramps[k][2]['colors'],ramps['figc_a'][2]['colors']) for k in cfg['variants'])
print('GEAR_TEXTURES',list(tiles))
