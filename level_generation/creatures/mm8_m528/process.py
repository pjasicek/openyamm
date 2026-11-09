"""Offline m528 effect matting, exact layout registration and preview evidence."""
from pathlib import Path
import json,hashlib,importlib.util,argparse,datetime
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
HERE=ROOT.parent

def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
queue=module('queue',HERE/'mm8_restore_queue.py');matte=module('matte',ROOT/'matte.py')
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def spill(im):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=250)<=4)|(alpha<255));score=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1])*alpha/255*band;y,x=np.unravel_index(np.argmax(score),score.shape)
 return dict(max_score=float(score.max()),candidates_above_12=int((score>12).sum()),position=[int(x),int(y)],band_px=4)
def fix(im,repair_warm=False):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];band=(alpha>0)&((ndimage.distance_transform_edt(alpha>=250)<=4)|(alpha<255));excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-8)*band;c[:,:,0]-=excess;c[:,:,2]-=excess
 pale=(c@np.array([.2126,.7152,.0722])>110)&((c.max(axis=2)-c.min(axis=2))/np.maximum(c.max(axis=2),1)<.30);selected=band&pale&(c[:,:,1]>np.maximum(c[:,:,0],c[:,:,2]));c[:,:,1][selected]=np.maximum(c[:,:,0],c[:,:,2])[selected]
 # Demonstrated orange/pink remnant on pale electrical filaments: constrain
 # only warm contour chroma to native ivory/straw gold, preserving luminance.
 warm=band&(c[:,:,0]>1.08*c[:,:,1])&(c[:,:,1]>35)&repair_warm
 target=c.copy();target[:,:,0]=np.minimum(target[:,:,0],1.06*target[:,:,1]);target[:,:,2]=np.maximum(target[:,:,2],.80*target[:,:,1])
 lum=c@np.array([.2126,.7152,.0722]);tlum=target@np.array([.2126,.7152,.0722]);target*=np.divide(lum,np.maximum(tlum,1))[:,:,None]
 c[warm]=target[warm]
 a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8);a[alpha==0]=0;return Image.fromarray(a)
def run(batch,raw,prompt,identity=None):
 inv=json.loads((ROOT/'sources.json').read_text());batches=json.loads((ROOT/'batches.json').read_text());b=batches[batch];im=Image.open(ROOT/'raw'/raw).convert('RGB');cols,rows=b['columns'],b['rows'];cw,ch=im.width/cols,im.height/rows
 ratio=b['cell_size'][0]/cw;assert abs(ratio-b['cell_size'][1]/ch)<.005,'Generated layout aspect ratio changed'
 for d in ('cleaned','aligned_2x','review','checkpoints'):(ROOT/d).mkdir(exist_ok=True)
 reg=json.loads((ROOT/'registration.json').read_text()) if (ROOT/'registration.json').exists() else {};contact=Image.new('RGB',(320*len(b['frames']),700),(35,35,35));draw=ImageDraw.Draw(contact)
 for i,n in enumerate(b['frames']):
  rect=[round(i%cols*cw),round(i//cols*ch),round((i%cols+1)*cw),round((i//cols+1)*ch)];clean,stats=matte.extract(im.crop(rect));clean=fix(clean,n.startswith('m528w'));bb=clean.getchannel('A').getbbox();assert bb and 0<bb[0]<bb[2]<clean.width and 0<bb[1]<bb[3]<clean.height,(n,bb)
  clean.save(ROOT/f'cleaned/{n}.png');scaled=fix(clean.convert('RGBa').resize((round(clean.width*ratio),round(clean.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA'),n.startswith('m528w'))
  layout=b['layout'][i];origin=layout['source_origin'];cell=layout['cell_xywh'];offset=[cell[0]-origin[0],cell[1]-origin[1]];native=queue.native(ROOT,n);bounds=scaled.getchannel('A').getbbox();canvas_origin=[min(0,offset[0]+bounds[0]-4),min(0,offset[1]+bounds[1]-4)];size=[max(native.width*2,offset[0]+bounds[2]+4)-canvas_origin[0],max(native.height*2,offset[1]+bounds[3]+4)-canvas_origin[1]]
  aligned=Image.new('RGBA',size);aligned.paste(scaled,(offset[0]-canvas_origin[0],offset[1]-canvas_origin[1]));aligned.save(ROOT/f'aligned_2x/{n}.png');sb=native.getchannel('A').getbbox()
  reg[n]=dict(batch=batch,raw=raw,extraction_xyxy=rect,scale_to_2x=ratio,translation_px=offset,canvas_origin_px=canvas_origin,aligned_size_px=size,logical_size=list(native.size),source_sha256=inv['sources'][n]['sha256'],raw_clip=False,generated_visible_height=bb[3]-bb[1],native_visible_height=sb[3]-sb[1],edge_cleaned=spill(clean),edge_export=spill(aligned))
  for row,pic in enumerate((native.resize((native.width*2,native.height*2),Image.Resampling.NEAREST),aligned)):
   bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);bg.thumbnail((310,310),Image.Resampling.LANCZOS);contact.paste(bg.convert('RGB'),(i*320,row*350+30));draw.text((i*320+4,row*350+5),n+(' native' if row==0 else ' restored 2x'),fill='white')
 save(ROOT/'registration.json',reg);contact.save(ROOT/f'review/{batch}_native_restored.png')
 refs=(['raw/identity_v2.png','references/identity_matte.png'] if raw=='identity_v3.png' else ['raw/identity_v1.png']) if batch=='identity' else [f'references/{batch}_matte.png']
 if identity:refs.append(identity)
 g=json.loads((ROOT/'generation.json').read_text()) if (ROOT/'generation.json').exists() else {'tool':'built-in image_gen','batches':{}}
 g['batches'][batch]=dict(raw={'path':'raw/'+raw,'sha256':queue.sha(ROOT/'raw'/raw)},prompt={'path':'prompts/'+prompt,'sha256':queue.sha(ROOT/'prompts'/prompt)},references=[dict(path=p,sha256=queue.sha(ROOT/p)) for p in refs],dimensions=list(im.size),status='processed_unreviewed');save(ROOT/'generation.json',g)
 batches[batch].update(state='processed_unreviewed',selected_raw=raw);save(ROOT/'batches.json',batches)
 save(ROOT/'processing.json',dict(runtime_scale=2,registration='Exact native reference cell/source origin; shared scale from generated grid dimensions. No per-pose silhouette fit or recentering.',tone_multiplier=1,matte='Local magenta foreground/background unmix; no intended magenta in palette 528.',filter='Premultiplied-alpha Lanczos',edge='4px contour magenta excess limit 8; neutral pale compensation cast; demonstrated warm filament fringe R/G>1.08 and G>35 constrained to R/G<=1.06 and B/G>=.80 preserving luminance; alpha unchanged',disconnected_sparks='Retained; no connected-component removal'))
 p=HERE/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();ledger['families']['m528'].update(status='partial',processed_frames=len(reg),resume='Review Wisp identity, then process the remaining exact native batches. Preserve native Center, Lit, glow_radius and descriptor scale differences.');ledger['summary']={s:sum(f['status']==s for f in ledger['families'].values()) for s in ('pending','partial','validated','blocked')};save(p,ledger)
 print(batch,len(b['frames']),'processed; total',len(reg),'of',len(inv['sources']))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('raw');p.add_argument('prompt');p.add_argument('--identity');a=p.parse_args();run(a.batch,a.raw,a.prompt,a.identity)
