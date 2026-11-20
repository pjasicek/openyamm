"""Extract compact generated sheets, preserving native coordinates and measuring delivered sampling."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.optimize import minimize
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import process,calibrate,tone
ROOT=process.ROOT;D=ROOT/'detail_upgrade'

def run(key,raw_name,prompt_name=None):
 data=json.loads((D/'jobs.json').read_text());job=data['jobs'][key];names=job['frames'];raw=Image.open(D/'raw'/raw_name);cw=raw.width/job['columns'];ch=raw.height;crop=job['native_canvas_crop_2x'];tw,th=crop[2]-crop[0],crop[3]-crop[1];rx,ry=tw/cw,th/ch
 assert abs(rx/ry-1)<.03,('returned layout aspect needs explicit review',raw.size,job['reference_cell_size_px'])
 ratio=(rx+ry)/2;arts=[];natives=[];records=[]
 for f in ['cleaned','registered_2x','toned_2x','review/registration']:(D/f).mkdir(parents=True,exist_ok=True)
 for i,name in enumerate(names):
  rect=[round(i*cw),0,round((i+1)*cw),ch];clean=process.extract(raw.crop(rect),name);bb=clean.getchannel('A').getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<clean.width and bb[3]<clean.height,(name,bb)
  clean.save(D/'cleaned'/f'{name}.png');im=clean.convert('RGBa').resize((round(clean.width*ratio),round(clean.height*ratio)),Image.Resampling.LANCZOS).convert('RGBA');canvas=Image.new('RGBA',(576,576));canvas.paste(im,(round(crop[0]+(tw-im.width)/2),round(crop[1]+(th-im.height)/2)));arts.append(canvas)
  native=Image.new('RGBA',(576,576));native.paste(process.queue.native(ROOT,name).resize((512,512),Image.Resampling.NEAREST),(32,32));natives.append(native);records.append({'raw_cell_xyxy':rect,'raw_visible_xyxy':bb,'raw_size_px':clean.size,'reference_native_crop_2x':crop,'normalization_scale_to_2x':ratio})
 masks=[calibrate.body(a) for a in arts];targets=[calibrate.body(a) for a in natives]
 def objective(v):
  num=den=0
  for a,b in zip(masks,targets):
   w=calibrate.warp(a,v);num+=2*(w*b).sum();den+=(w*w+b*b).sum()
  return 1-num/max(den,1e-9)+.02*(v[0]-1)**2
 values=job.get('accepted_calibration')
 if values is None:values=minimize(objective,[1,0,0],method='Powell',bounds=[(.7,1.1),(-15,15),(-15,15)],options={'maxiter':50,'xtol':.0001}).x.tolist()
 scale,dx,dy=values;sampling=2/(ratio*scale);assert sampling>=job['minimum_generated_pixels_per_native_pixel'],('insufficient generated detail sampling',key,sampling)
 regs=json.loads((D/'registration.json').read_text()) if (D/'registration.json').exists() else {};sheet=Image.new('RGB',(384*len(names),1176),(35,35,35));draw=ImageDraw.Draw(sheet)
 for i,(name,art,native,record) in enumerate(zip(names,arts,natives,records)):
  out=process.fix(art.convert('RGBa').transform((576,576),Image.Transform.AFFINE,(1/scale,0,288-(288+4.5*dx)/scale,0,1/scale,288-(288+4.5*dy)/scale),Image.Resampling.BICUBIC).convert('RGBA'),name);bb=out.getchannel('A').getbbox();assert bb[0]>3 and bb[1]>3 and bb[2]<573 and bb[3]<573,(name,bb)
  out.save(D/'registered_2x'/f'{name}.png');a=np.array(out);rgb=a[:,:,:3].astype(float);alpha=a[:,:,3]/255;n=np.array(native);graded=tone.field(n[:,:,:3].astype(float),n[:,:,3]/255)+.7*(rgb-tone.field(rgb,alpha));a[:,:,:3]=np.round(graded).clip(0,255).astype(np.uint8);final=process.fix(Image.fromarray(a),name);final.save(D/'toned_2x'/f'{name}.png')
  assert np.array_equal(np.asarray(final)[:,:,3],np.asarray(out)[:,:,3]);edges={'registered':process.spill(out,name),'toned':process.spill(final,name)};assert all(v['max_score']==0 for v in edges.values())
  regs[name]={**record,'batch':key,'raw':raw_name,'shared_calibration':values,'generated_pixels_per_native_pixel':sampling,'canvas_origin_px':[-32,-32],'aligned_size_px':[576,576],'logical_size':[256,256],'edges':edges,'state':'processed_unreviewed'}
  overlay=np.zeros((128,128,3),np.uint8);overlay[:,:,0]=np.round(targets[i]*255).clip(0,255).astype(np.uint8);overlay[:,:,1]=np.round(calibrate.warp(masks[i],values)*255).clip(0,255).astype(np.uint8)
  for row,pic in enumerate([native,final,Image.fromarray(overlay).resize((576,576))]):
   bg=Image.new('RGBA',pic.size,(35,35,35,255));bg.alpha_composite(pic.convert('RGBA'));sheet.paste(bg.resize((384,384)).convert('RGB'),(384*i,392*row+8));draw.text((384*i+4,392*row+3),name+' '+['native','refined 2x','native red / art green'][row],fill='white')
 sheet.save(D/'review/registration'/f'{key}.png');process.save(D/'registration.json',regs)
 prompt=prompt_name or job['prompt'];refs=job.get('generation_references',job['references']);generation={'raw':{'path':'raw/'+raw_name,'sha256':process.queue.sha(D/'raw'/raw_name)},'prompt':{'path':prompt,'sha256':process.queue.sha(D/prompt)},'references':[{'path':p,'sha256':process.queue.sha(D/p)} for p in refs],'dimensions':list(raw.size),'generated_pixels_per_native_pixel':sampling,'shared_calibration':values,'status':'processed_unreviewed'}
 job.update(status='processed_unreviewed',selected_raw=raw_name,generation=generation);process.save(D/'jobs.json',data);print(key,len(names),'frames;',round(sampling,2),'generated pixels/native pixel;',values,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('job');p.add_argument('raw');p.add_argument('--prompt');a=p.parse_args();run(a.job,a.raw,a.prompt)
