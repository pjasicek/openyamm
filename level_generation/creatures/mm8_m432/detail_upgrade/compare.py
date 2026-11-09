"""Review detail trials at unchanged native 2x placement; no active package mutation."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import minimize
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import process,calibrate,tone
ROOT=process.ROOT;D=ROOT/'detail_upgrade'
batches=json.loads((ROOT/'batches.json').read_text())
results={};rows=[]
for trial,names,cols in [('identity_front_v1',batches['identity']['frames'][:1],1),('attack_front_pair_v3',batches['native_a_v0']['frames'][:2],2)]:
 raw=Image.open(D/'raw'/f'{trial}.png');cw=raw.width/cols;ch=raw.height;ratio=540/max(cw,ch);arts=[];targets=[];natives=[]
 for i,n in enumerate(names):
  a=process.extract(raw.crop((round(i*cw),0,round((i+1)*cw),ch)),n)
  a=a.convert('RGBa').resize((round(a.width*ratio),round(a.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA')
  canvas=Image.new('RGBA',(576,576));canvas.paste(a,((576-a.width)//2,(576-a.height)//2));arts.append(canvas)
  native=Image.new('RGBA',(576,576));native.paste(process.queue.native(ROOT,n).resize((512,512),Image.Resampling.NEAREST),(32,32));natives.append(native);targets.append(calibrate.body(native))
 masks=[calibrate.body(a) for a in arts]
 def objective(v):
  num=den=0
  for a,b in zip(masks,targets):
   w=calibrate.warp(a,v);num+=2*(w*b).sum();den+=(w*w+b*b).sum()
  return 1-num/max(den,1e-9)
 values=minimize(objective,[.85,0,0],method='Powell',bounds=[(.5,1.1),(-25,25),(-25,25)],options={'maxiter':60,'xtol':.0001}).x.tolist();scale,dx,dy=values
 results[trial]={'frames':names,'generated_sheet_px':raw.size,'shared_normalization_scale':ratio,'shared_registration_values':values,'coverage_error':objective(values),'status':'requires_visual_review','method':'One common uniform scale and translation for the complete trial; native logical geometry remains 256x256 at 2x. No per-pose transforms.'}
 for n,art,native in zip(names,arts,natives):
  out=art.convert('RGBa').transform((576,576),Image.Transform.AFFINE,(1/scale,0,288-(288+4.5*dx)/scale,0,1/scale,288-(288+4.5*dy)/scale),Image.Resampling.BICUBIC).convert('RGBA');out=process.fix(out,n)
  box=out.getchannel('A').getbbox();assert box[0]>3 and box[1]>3 and box[2]<573 and box[3]<573
  old=Image.open(ROOT/'registered_2x'/f'{n}.png').convert('RGBA')
  def grade(im):
   a=np.array(im);rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]/255;src=np.array(native)
   corrected=tone.field(src[:,:,:3].astype(float),src[:,:,3]/255)+.7*(rgb-tone.field(rgb,alpha));a[:,:,:3]=np.round(corrected).clip(0,255).astype(np.uint8);return process.fix(Image.fromarray(a),n)
  old=grade(old);out=grade(out);out.save(D/'review'/f'{n}_trial_2x.png')
  boxes=[a.getchannel('A').getbbox() for a in [native,old,out]];crop=(min(a[0] for a in boxes)-8,min(a[1] for a in boxes)-8,max(a[2] for a in boxes)+8,max(a[3] for a in boxes)+8)
  rows.append((n,[im.crop(crop) for im in [native,old,out]]))
cellw=max(im.width for _,ims in rows for im in ims)+20;heights=[max(im.height for im in ims)+40 for _,ims in rows];sheet=Image.new('RGB',(3*cellw,sum(heights)),(35,35,35));draw=ImageDraw.Draw(sheet);y=0
for (n,ims),h in zip(rows,heights):
 for i,im in enumerate(ims):
  draw.text((i*cellw+5,y+5),n+' '+['native 2x','earlier restoration','higher-detail trial'][i],fill='white');sheet.paste(im,(i*cellw+(cellw-im.width)//2,y+30),im)
 y+=h
sheet.save(D/'review/runtime_comparison.png');(D/'review/registration.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
