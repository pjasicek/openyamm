"""Native inventory and effect maps from the retained m528 restoration; no generated anatomy."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import map_coordinates

P=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm8_m528_claude')
R=P.parents[2]; S=P.parent/'mm8_m528'
for d in ['scripts','source','textures','work','export','review/viewer/feedback','review/shots']:
    (P/d).mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p,d): p.write_text(json.dumps(d,indent=2)+'\n')
sources=json.loads((S/'sources.json').read_text()); manifest=json.loads((S/'manifest.json').read_text())
assert len(sources['sources'])==56
for name,s in sources['sources'].items():
    assert sha(R/s['path'])==s['sha256'],name
actions={}
for name,a in manifest['animations']['97']['actions'].items():
    frames=a['views']['0']
    actions[name]={'seconds':sum(f['duration_ms'] for f in frames)/1000,
        'frames':[{'name':f['frame'],'seconds':f['duration_ms']/1000,'glow':f['glow_radius']} for f in frames],
        'playback':a['playback']}
save_json(P/'source/native_inventory.json',{'source_manifest_sha256':sha(S/'sources.json'),
    'frames':sources['sources'],'actions':actions,'tiers':manifest['variants']['actors'],
    'observed':'One camera-facing source view reused in all eight directions. Center anchored, Lit. Grey smoky ring, gold core, ivory sparks; warm expanding attack, smoke dispersion, empty corpse.',
    'inferred':'Rotational volume and orbit paths are authored depth for the front-only art. Ring is translucent swirling smoke, not metal.'})

def load(name): return Image.open(S/'aligned_2x'/f'{name}.png').convert('RGBA')
sheet=Image.new('RGB',(1600,3*224),(40,42,46));draw=ImageDraw.Draw(sheet)
for row,act in enumerate(['standing','attack','death']):
    names=[f['name'] for f in actions[act]['frames'] if f['name']]
    names=[names[round(i*(len(names)-1)/7)] for i in range(8)]
    for col,name in enumerate(names):
        im=load(name);im.thumbnail((190,190));sheet.paste(im,(col*200,row*224+22),im)
        draw.text((col*200+4,row*224+4),name,fill='white')
sheet.save(P/'review/native_actions.png')

# A tiling turbulent smoke field in the measured native grey palette. Direct torus projection of
# the tiny front-only ring stretched its baked creases into strips, so retain colour and author volume.
from scipy.ndimage import gaussian_filter
im=np.asarray(load('m528wa0'),dtype=float)/255
patch=im[105:150,94:165];lum=patch[...,:3].mean(-1)
pixels=patch[...,:3][(patch[...,3]>.7)&(lum>.12)&(lum<.53)&(patch[...,0]<patch[...,2]*1.06)]
pixels=pixels[np.argsort(pixels.mean(-1))];dark,light=pixels[int(len(pixels)*.12)],pixels[int(len(pixels)*.90)]
rng=np.random.default_rng(528);noise=np.zeros((256,512))
for sigma,gain in [(28,1),(12,.60),(5,.32),(2,.12)]:
    layer=gaussian_filter(rng.normal(size=noise.shape),(sigma,sigma*1.8),mode='wrap')
    noise+=gain*layer/max(layer.std(),1e-8)
v,u=np.mgrid[0:256,0:512]
noise=map_coordinates(noise,[v+12*np.sin(u/512*6*np.pi),u+20*np.sin(v/256*4*np.pi)],order=1,mode='grid-wrap')
tone=np.clip(.48+.18*noise,0,1);out=np.empty((256,512,4))
out[...,:3]=dark+(light-dark)*tone[...,None];out[...,3]=np.clip(.64+.15*noise,.12,.92)
Image.fromarray(np.uint8(np.clip(out,0,1)*255)).save(P/'textures/m528_smoke.png')

# The atlas contains small effect fragments, never a whole creature on a card.
atlas=Image.new('RGBA',(1024,1024)); tiles={}; receipts=[]
def tile(index,name,im):
    ratio=232/max(im.size);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
    x=(index%4)*256+(256-im.width)//2;y=(index//4)*256+(256-im.height)//2
    atlas.paste(im,(x,y));tiles[name]=index
def crop(index,name,frame,box):
    im=load(frame).crop(box);a=np.asarray(im,dtype=float).copy();h,w=a.shape[:2]
    if name.startswith('spark'):
        lum=a[...,:3].mean(-1);a[...,3]*=np.clip((lum-100)/70,0,1)
    ey,ex=np.indices((h,w));edge=np.minimum.reduce([ex,w-1-ex,ey,h-1-ey])
    a[...,3]*=np.clip(edge/3,0,1)
    tile(index,name,Image.fromarray(a.astype('uint8')));receipts.append({'tile':name,'source':frame,'box':box,'sha256':sha(S/'aligned_2x'/f'{frame}.png')})
for i,(frame,box) in enumerate([
    ('m528wa0',(87,60,147,108)),('m528wa0',(62,151,120,215)),
    ('m528wc0',(150,85,205,142)),('m528we0',(65,55,126,111)),
    ('m528wg0',(152,139,211,200)),('m528wi0',(42,110,98,170))]):
    crop(i,f'spark{i}',frame,box)
# Smoke puffs from the source's scattered death: pick substantial warm connected components outside the ring.
from scipy.ndimage import label,find_objects,binary_opening
death=np.asarray(load('m528di0'));rgb=death[...,:3].astype(float);yy,xx=np.indices(death.shape[:2])
warm=(rgb[...,0]>rgb[...,2]*1.12)&(death[...,3]>40)&(((xx-128)**2+(yy-128)**2)>55**2)
labels,count=label(binary_opening(warm,iterations=1));boxes=[]
for n,b in enumerate(find_objects(labels),1):
    if b and (labels[b]==n).sum()>18:
        boxes.append(((labels[b]==n).sum(),b))
assert len(boxes)>=4,'Need distinct native smoke puffs'
for i,(_,b) in enumerate(sorted(boxes,reverse=True,key=lambda p:p[0])[:6]):
    yb,xb=b;box=(max(0,xb.start-3),max(0,yb.start-3),min(death.shape[1],xb.stop+3),min(death.shape[0],yb.stop+3))
    crop(6+i,f'smoke{i}','m528di0',box)
# Smooth halo/core profiles are sampled in the native gold/ivory colours, with analytic soft alpha.
yy,xx=np.mgrid[-1:1:256j,-1:1:256j];rr=xx*xx+yy*yy
for idx,name,colour,width in [(12,'core',(255,220,91),4.8),(13,'halo',(255,197,73),3.3),
                               (14,'flash',(255,239,194),5.4),(15,'ember',(179,221,255),8)]:
    a=np.maximum(0,np.exp(-rr*width)-np.exp(-width))/(1-np.exp(-width))
    rgba=np.empty((256,256,4));rgba[...,:3]=colour;rgba[...,3]=a*255
    if name in ('core','flash'):rgba[...,:3]=rgba[...,:3]*(1-a[...,None])+np.array([255,255,240])*a[...,None]
    tile(idx,name,Image.fromarray(rgba.astype('uint8')))
# Native hot surface, softly clipped to the core, for the expanding attack shell.
flash=load('m528ag0').crop((63,52,193,182));ar=np.array(flash,dtype=float)
yy,xx=np.mgrid[-1:1:complex(0,ar.shape[0]),-1:1:complex(0,ar.shape[1])]
ar[...,3]*=np.clip((1-xx*xx-yy*yy)*6,0,1)
tile(14,'flash',Image.fromarray(ar.astype('uint8')))
atlas.save(P/'textures/m528_fx.png')
Image.new('L',(1024,1024),11).save(P/'textures/m528_material_classes.png')
save_json(P/'textures/provenance.json',{'route':'Effect-bodied playbook: retained restored fragments and analytic light falloff',
    'restoration':str(S.relative_to(R)),'tiles':tiles,'crops':receipts,'appearance':'Identical shared palette 528 for all tiers; no recolour mask or ramp needed.'})
state=json.loads((P/'creature_3d_progress.json').read_text())
state.update(scope='complete_production',stage='model_and_motion',substep='Native inventory verified; procedural effect maps prepared',
    user_direction='Reactor + Air Elemental for effects; new floating spark-ring body animation.',
    required_components=[{'id':n,'artifact_role':n,'required':True,'status':'in_progress'} for n in ['smoky_ring','gold_core','orbiting_sparks','attack_flash','death_smoke']],
    route='Local effect-bodied route. No Meshy or HD masters. Reactor glow and air-elemental blended-surface methods only; m528 geometry and motion are new.',
    next_action={'owner':'codex','action':'Build and inspect hovering and attack pilots, then complete the remaining motion and runtime checks.'},
    acceptance={'technical':'in_progress','agent_visual':'in_progress','user_artistic':'not_recorded'},correction_ledger=[])
save_json(P/'creature_3d_progress.json',state)
print('Verified 56 source frames; native actions', {k:v['seconds'] for k,v in actions.items()})
