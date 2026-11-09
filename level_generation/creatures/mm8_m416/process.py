"""Native-layout Pirate Crossbow Female extraction, palette-aware edge repair and fixed tone."""
from pathlib import Path
import json,importlib.util,argparse,datetime
import numpy as np
from scipy import ndimage as ndi
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
queue=module('queue',ROOT.parent/'mm8_restore_queue.py')
def save(p,d):p.parent.mkdir(exist_ok=True,parents=True);p.write_text(json.dumps(d,indent=2)+'\n')
def edge_limits(name=None):
 if name is None:return {'magenta': 51, 'cyan': 38, 'green': 20}
 return json.loads((ROOT/'native_frame_edge_limits.json').read_text())[name]
def spill(im,name=None):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];limits=edge_limits(name)
 band=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
 magenta=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-limits['magenta'])*alpha/255*band
 cyan=np.maximum(0,np.minimum(c[:,:,1],c[:,:,2])-c[:,:,0]-limits['cyan'])*alpha/255*band
 green=np.maximum(0,c[:,:,1]-np.maximum(c[:,:,0],c[:,:,2])-limits['green'])*alpha/255*band
 score=np.maximum(np.maximum(magenta,cyan),green);y,x=np.unravel_index(np.argmax(score),score.shape)
 return {'max_score':float(score.max()),'max_magenta':float(magenta.max()),'max_cyan':float(cyan.max()),'max_green':float(green.max()),'candidates_above_12':int((score>12).sum()),'position':[int(x),int(y)],'native_allowances':limits,'band_px':4}
def fix(im,name=None):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3];limits=edge_limits(name)
 band=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
 excess=np.maximum(0,np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1]-limits['magenta'])*band
 c[:,:,0]-=excess;c[:,:,2]-=excess
 cyan=band&(c[:,:,1]>c[:,:,0]+limits['cyan'])&(c[:,:,2]>c[:,:,0]+limits['cyan'])
 c[:,:,2][cyan]=c[:,:,0][cyan]+limits['cyan']
 c[:,:,1][band]=np.minimum(c[:,:,1],np.maximum(c[:,:,0],c[:,:,2])+limits['green'])[band]
 a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8);a[alpha==0]=0
 return Image.fromarray(a)
def extract(im,name=None):
 c=np.array(im.convert('RGB'),float)/255;dom=np.minimum(c[:,:,0],c[:,:,2])-c[:,:,1];core=dom<=max(20,edge_limits(name)['magenta']+5)/255;bg=(dom>210/255)&(c[:,:,0]>.9)&(c[:,:,2]>.9)&(c[:,:,1]<.1);dist,idx=ndi.distance_transform_edt(~core,return_indices=True);_,bi=ndi.distance_transform_edt(~bg,return_indices=True);f=c[idx[0],idx[1]];b=c[bi[0],bi[1]];v=f-b;alpha=np.clip(np.sum((c-b)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-8),0,1);alpha[core]=1;alpha[bg|(dist>7)]=0;rgb=(c-(1-alpha[:,:,None])*b)/np.maximum(alpha[:,:,None],1/255);rgb[core]=c[core];rgb[alpha==0]=0;out=Image.fromarray(np.dstack([np.round(np.clip(rgb,0,1)*255),np.round(alpha*255)]).astype(np.uint8));return fix(out,name)
def mean_luma(im):
 a=np.asarray(im).astype(float);weight=a[:,:,3]/255;return float(((a[:,:,:3]@np.array([.2126,.7152,.0722]))*weight).sum()/weight.sum())
def run(key,raw,prompt,identity=None):
 s=json.loads((ROOT/'sources.json').read_text());batches=json.loads((ROOT/'batches.json').read_text());b=batches[key];sheet=Image.open(ROOT/'raw'/raw);cw=sheet.width/b['columns'];ch=sheet.height/b['rows'];ratio=b['cell_size'][0]/cw;assert abs(ratio-b['cell_size'][1]/ch)<.005
 for folder in ['cleaned','aligned_2x','review','checkpoints']:(ROOT/folder).mkdir(exist_ok=True)
 cleanframes=[]
 for i,n in enumerate(b['frames']):
  rect=[round(i%b['columns']*cw),round(i//b['columns']*ch),round((i%b['columns']+1)*cw),round((i//b['columns']+1)*ch)];im=extract(sheet.crop(rect),n);bb=im.getchannel('A').getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<im.width and bb[3]<im.height,(n,bb);cleanframes.append((n,im,rect))
 tp=ROOT/'tone_settings.json'
 if tp.exists():tone=json.loads(tp.read_text())
 else:
  assert key=='identity';ratios=[mean_luma(queue.native(ROOT,n))/mean_luma(im) for n,im,_ in cleanframes];tone={'multiplier':float(np.median(ratios)),'method':'Single median native/generated mean-luminance ratio across five identity views, frozen for all actions; no per-frame matching.','identity_ratios':ratios};save(tp,tone)
 reg=json.loads((ROOT/'registration.json').read_text()) if (ROOT/'registration.json').exists() else {};contact=Image.new('RGB',(512*len(cleanframes),1100),(35,35,35));draw=ImageDraw.Draw(contact)
 for i,(n,im,rect) in enumerate(cleanframes):
  rawbb=im.getchannel('A').getbbox();a=np.array(im);a[:,:,:3]=np.round(a[:,:,:3].astype(float)*tone['multiplier']).clip(0,255).astype(np.uint8);im=fix(Image.fromarray(a),n);im.save(ROOT/f'cleaned/{n}.png');scaled=fix(im.convert('RGBa').resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA'),n)
  layout=b['layout'][i];offset=[layout['cell_xywh'][0]-layout['source_origin'][0],layout['cell_xywh'][1]-layout['source_origin'][1]]
  row_shift=b.get('row_translation_2x_px',{}).get(str(i//b['columns']),[0,0]);offset=[v+row_shift[j] for j,v in enumerate(offset)]
  if b.get('uniform_layout_scale'):
   factor=b['uniform_layout_scale'];old_size=scaled.size;scaled=fix(scaled.convert('RGBa').resize(tuple(round(v*factor) for v in old_size),Image.Resampling.LANCZOS).convert('RGBA'),n);offset=[v+round((old_size[j]-scaled.size[j])/2) for j,v in enumerate(offset)]
  bb=scaled.getchannel('A').getbbox();origin=[min(0,offset[0]+bb[0]-4),min(0,offset[1]+bb[1]-4)];size=[max(512,offset[0]+bb[2]+4)-origin[0],max(512,offset[1]+bb[3]+4)-origin[1]];aligned=Image.new('RGBA',size);aligned.paste(scaled,(offset[0]-origin[0],offset[1]-origin[1]));aligned.save(ROOT/f'aligned_2x/{n}.png');native=queue.native(ROOT,n);nb=native.getchannel('A').getbbox()
  reg[n]={'batch':key,'raw':raw,'extraction_xyxy':rect,'scale_to_2x':ratio,'uniform_layout_scale':b.get('uniform_layout_scale',1),'translation_px':offset,'canvas_origin_px':origin,'aligned_size_px':size,'logical_size':[256,256],'source_sha256':s['sources'][n]['sha256'],'raw_clip':False,'generated_visible_height':rawbb[3]-rawbb[1],'native_visible_height':nb[3]-nb[1],'edge_cleaned':spill(im,n),'edge_export':spill(aligned,n)}
  for row,pic in enumerate([native.resize((512,512),Image.Resampling.NEAREST),aligned]):
   bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic);contact.paste(bg.convert('RGB'),(i*512,row*550+30));draw.text((i*512+5,row*550+5),n+(' native' if row==0 else ' restored 2x'),fill='white')
 contact.save(ROOT/f'review/{key}_native_restored.png');save(ROOT/'registration.json',reg)
 refs=b.get('generation_references',[f'references/{key}_matte.png']+([identity] if identity else []));g=json.loads((ROOT/'generation.json').read_text()) if (ROOT/'generation.json').exists() else {'tool':'built-in image_gen','batches':{}};g['batches'][key]={'raw':{'path':'raw/'+raw,'sha256':queue.sha(ROOT/'raw'/raw)},'prompt':{'path':'prompts/'+prompt,'sha256':queue.sha(ROOT/'prompts'/prompt)},'references':[{'path':p,'sha256':queue.sha(ROOT/p)} for p in refs],'dimensions':list(sheet.size),'status':'processed_unreviewed'};save(ROOT/'generation.json',g)
 batches[key].update(state='processed_unreviewed',selected_raw=raw);save(ROOT/'batches.json',batches);save(ROOT/'processing.json',{'runtime_scale':2,'registration':'Exact common native cell/source origin, no per-frame size normalization.','tone':tone,'matte':'Local magenta matte unmix, core tolerance max(20, native frame magenta excess + 5)/255; native crossbow, quiver, bandanna and clothing contours retained.','filter':'Premultiplied-alpha Lanczos','edge':'Each frame uses its measured native magenta/cyan/green opponent limits in 4px contours, including partial alpha. RGB-only repair retains gray-white clothing, brown boots, steel crossbow and bolt quiver, and green bandanna and sash; alpha unchanged.'})
 p=ROOT.parent/'mm8_remaining/progress.json';ledger=json.loads(p.read_text());ledger['families']['m416'].update(status='partial',processed_frames=len(reg),resume='Review current native/restored contacts, reuse accepted identity and continue pending batches; export and validate all 160 native files.');ledger['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p.write_text(json.dumps(ledger,indent=2)+'\n');print(key,'processed;',len(reg),'of 159 unique frames; frozen tone',tone['multiplier'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('batch');p.add_argument('raw');p.add_argument('prompt');p.add_argument('--identity');a=p.parse_args();run(a.batch,a.raw,a.prompt,a.identity)
