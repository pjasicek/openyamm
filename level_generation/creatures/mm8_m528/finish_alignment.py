"""Frozen native-core calibration and demonstrated pale-filament fringe repair."""
import json,numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from process import ROOT,save,spill,fix,queue

def filament_repair(im,protect_body=True):
 a=np.array(im);c=a[:,:,:3].astype(float);alpha=a[:,:,3]
 radius=max(2,round(im.width/320*6));y,x=np.ogrid[-radius:radius+1,-radius:radius+1];disk=x*x+y*y<=radius*radius
 body=ndi.binary_opening(alpha>128,structure=disk);body=ndi.binary_dilation(body,structure=disk)
 edge=(alpha>0)&((ndi.distance_transform_edt(alpha>=250)<=4)|(alpha<255))
 warm=edge&(~body if protect_body else True)&(c[:,:,0]>1.08*c[:,:,1])&(c[:,:,0]>1.08*c[:,:,2])&(c[:,:,1]>35)
 target=c.copy();target[:,:,0]=np.minimum(target[:,:,0],1.06*target[:,:,1]);target[:,:,2]=np.maximum(target[:,:,2],.80*target[:,:,1]);lum=c@np.array([.2126,.7152,.0722]);tlum=target@np.array([.2126,.7152,.0722]);target*=np.divide(lum,np.maximum(tlum,1))[:,:,None]
 c[warm]=target[warm];a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8)
 return Image.fromarray(a),int(warm.sum())

def core_tone(im):
 a=np.array(im);c=a[:,:,:3].astype(float);g=np.maximum(c[:,:,1],1);lum=c@np.array([.2126,.7152,.0722]);radius=max(2,round(im.width/320*6));y,x=np.ogrid[-radius:radius+1,-radius:radius+1];disk=x*x+y*y<=radius*radius
 body=ndi.binary_opening(a[:,:,3]>128,structure=disk);body=ndi.binary_dilation(body,iterations=max(1,radius//2))
 weight=np.clip((1.08-c[:,:,0]/g)/.06,0,1)*np.clip((c[:,:,2]/g-.72)/.12,0,1)*np.clip((175-lum)/45,0,1)*body
 target=c*np.array([1.057,1,1.20]);tlum=target@np.array([.2126,.7152,.0722]);target*=np.divide(lum,np.maximum(tlum,1))[:,:,None];c=c*(1-weight[:,:,None])+target*weight[:,:,None];a[:,:,:3]=np.round(c).clip(0,255).astype(np.uint8)
 return Image.fromarray(a),Image.fromarray(np.round(weight*255).astype(np.uint8),'L')

def run():
 reg=json.loads((ROOT/'registration.json').read_text());batches=json.loads((ROOT/'batches.json').read_text());audit=json.loads((ROOT/'review/core_registration_audit.json').read_text())
 configpath=ROOT/'alignment_settings.json'
 if configpath.exists():config=json.loads(configpath.read_text())
 else:
  scales={'identity':1,'native_a_v0_0':.96,'native_a_v0_1':.85,'native_a_v0_2':1,'native_d_v0_0':.91,'native_d_v0_1':1,'native_d_v0_2':1,'native_w_v0_0':.86,'native_w_v0_1':1,'native_w_v0_2':.97}
  config={'method':'One reviewed core scale per batch, source-backed per-pose core landmarks; dispersed smoke and final glints retain native sheet registration. No per-frame size normalization.','frames':{},'batch_scales':scales,'calibration_evidence':'review/core_registration_audit.json','fringe_repair':'Pale warm filaments only: R/G>1.08 and R/B>1.08 outside opened/dilated body protection; clamp hue to ivory while retaining luminance and alpha. Cool sparks and native brown/orange core or smoke bodies protected.'}
  for key,b in batches.items():
   rows={r['frame']:r for r in audit.get(key,{}).get('frames',[])};s=scales[key]
   for n in b['frames']:
    r=reg[n];initial=np.array(r['translation_px'],float);size=np.array(r['aligned_size_px']);center=size/2
    if key=='identity':offset=initial
    elif n in rows:
     row=rows[n];native=np.array(row['native']);enh=np.array(row['enhanced']);nc=(native[:2]+native[2:])/2;ec=(enh[:2]+enh[2:])/2+np.array(r['canvas_origin_px']);offset=nc+(initial-ec)*s
    else:offset=center+(initial-center)*s
    config['frames'][n]={'scale_to_2x':r['scale_to_2x']*s,'translation_px':np.round(offset).astype(int).tolist()}
  save(configpath,config)
 for key,b in batches.items():
  sheet=Image.new('RGB',(256*len(b['frames']),580),(35,35,35));draw=ImageDraw.Draw(sheet)
  for i,n in enumerate(b['frames']):
   r=reg[n];settings=config['frames'][n];clean=Image.open(ROOT/f'cleaned/{n}.png').convert('RGBA');count=0
   quiet=n.startswith('m528w') or n in ['m528aa0','m528ab0','m528da0','m528db0'] or n.startswith('m528a') and n[5]>='m' or n.startswith('m528d') and n[5]>='l'
   if not n.startswith('m528w'):clean,count=filament_repair(clean,not quiet)
   clean,tonemask=core_tone(clean);(ROOT/'core_tone_masks').mkdir(exist_ok=True);tonemask.save(ROOT/f'core_tone_masks/{n}.png')
   (ROOT/'final_cleaned').mkdir(exist_ok=True);clean.save(ROOT/f'final_cleaned/{n}.png')
   scale=settings['scale_to_2x'];pic=clean.convert('RGBa').resize((round(clean.width*scale),round(clean.height*scale)),Image.Resampling.LANCZOS).convert('RGBA');pic=fix(pic,False)
   if not n.startswith('m528w'):pic,extra=filament_repair(pic,not quiet);count+=extra
   offset=settings['translation_px'];bb=pic.getchannel('A').getbbox();origin=[min(0,offset[0]+bb[0]-4),min(0,offset[1]+bb[1]-4)];size=[max(256,offset[0]+bb[2]+4)-origin[0],max(256,offset[1]+bb[3]+4)-origin[1]];out=Image.new('RGBA',size);out.paste(pic,(offset[0]-origin[0],offset[1]-origin[1]));out.save(ROOT/f'aligned_2x/{n}.png')
   r.update(scale_to_2x=scale,translation_px=offset,canvas_origin_px=origin,aligned_size_px=size,final_filament_repaired_pixels=count,edge_export=spill(out))
   for row,art in enumerate([queue.native(ROOT,n).resize((256,256),Image.Resampling.NEAREST),out]):
    bg=Image.new('RGBA',art.size,(35,35,35,255));bg.alpha_composite(art);sheet.paste(bg.convert('RGB'),(i*256,row*290+28));draw.text((i*256+4,row*290+4),n+(' native' if row==0 else ' restored'),fill='white')
  sheet.save(ROOT/f'review/{key}_final.png')
 save(ROOT/'registration.json',reg)
 settings=json.loads((ROOT/'processing.json').read_text());settings['registration']=config['method'];settings['alignment_settings']='alignment_settings.json';settings['final_filament_repair']=config['fringe_repair']+' Quiet-state filaments have no body exclusion; native hot flashes retain body exclusion.';settings['core_color_calibration']={'native_identity_sample_mean_rgb':[92.7176,90.3381,95.1367],'enhanced_identity_sample_mean_rgb':[84.2581,86.8453,76.2925],'fixed_chroma_multipliers':[1.057,1,1.20],'preserve_luminance':True,'coverage':'Enhanced broad body, neutral/cool chroma and shadow/midtone, highlights fade out 130–175. Warm smoke and flashes excluded. Masks in core_tone_masks/.'};save(ROOT/'processing.json',settings)
 print('Calibrated and repaired all',len(reg),'native frames; inspect final contacts before acceptance.')
if __name__=='__main__':run()
