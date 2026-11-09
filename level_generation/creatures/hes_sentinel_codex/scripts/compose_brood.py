"""Keep the egg-mound atlas; reserve a padded strip for the new stalks and bone supports."""
import io,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1]; R=P.parents[2]
sys.path.insert(0,str(R/'tools'))
sys.path.insert(0,str(R/'level_generation/creatures/claude_shared'))
from build_actor_lods import read_glb
from region_variants import fit_ramps
D,B=read_glb(P/'source/hes_egg_mound_export.glb')
images={}
for entry in D['images']:
 v=D['bufferViews'][entry['bufferView']]; start=v.get('byteOffset',0)
 images[entry['name']]=Image.open(io.BytesIO(B[start:start+v['byteLength']])).convert('RGB')
assert all(im.size==(1024,1024) for im in images.values())
base=np.array(images['hes_egg_mound_basecolor'])
# The untouched atlas occupies the left half. Three padded constant swatches occupy the right.
for suffix,fill in [('basecolor',(42,15,49)),('normal',(128,128,255)),('mr',(255,180,0))]:
 im=Image.new('RGB',(2048,1024),fill); im.paste(images['hes_egg_mound_'+suffix],(0,0))
 if suffix=='basecolor':
  im.paste((188,163,118),(1088,64,1472,960))
  im.paste((40,15,48),(1536,64,1984,448))
  im.paste((155,46,107),(1536,576,1984,960))
 im.save(P/'textures'/('brood_'+suffix+'.png'))
mask=np.zeros((1024,2048,4),np.uint8)
r,g,b=base.transpose(2,0,1).astype(float)
orange=(r>b*1.35)&(g>b*0.9)&(r>50)
mask[:,:1024,0]=orange*255;mask[:,:1024,1]=(~orange)*255
mask[:,1024:,1]=255
mask[64:960,1088:1472,1]=0;mask[64:960,1088:1472,2]=255
mask[576:960,1536:1984,1]=0;mask[576:960,1536:1984,0]=255
Image.fromarray(mask).save(P/'textures/brood_region_mask.png')
base=np.array(Image.open(P/'textures/brood_basecolor.png'),float)/255
magenta=base.copy()
# Orange living tissue becomes magenta on the Ganglion; stalks and bone keep their source palette.
magenta[:,:,0]=base[:,:,0]*0.9
magenta[:,:,1]=base[:,:,1]*0.35
magenta[:,:,2]=np.maximum(base[:,:,2],base[:,:,0]*0.65)
ramps={};report={}
for channel in range(3):
 fit,err=fit_ramps(base,{'orange':base,'magenta':magenta if channel==0 else base},mask[:,:,channel]/255)
 for variant,ramp in fit.items():ramps.setdefault(variant,[]).append(ramp)
 report[str(channel)]=err
for name,variant in [('egg_cluster','orange'),('brood_sac','orange'),('ganglion','magenta')]:
 cfg={'variants':[name],'materials':[{'base':mat,'prefix':mat,'mask':'brood_region_mask.png','ramps':{name:ramps[variant]}} for mat in ['Brood','Brood_Energy']]}
 (P/'textures'/(name+'_ramps.json')).write_text(json.dumps(cfg,indent=2)+'\n')
(P/'textures/ramps_fit.json').write_text(json.dumps(report,indent=2)+'\n')
assert (mask[:,:,3]==0).all()
print('Composed shared brood atlas and three region masks; alpha region unused.')
