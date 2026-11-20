"""Prepare compact native-coordinate detail refinements without replacing retained work."""
from pathlib import Path
import sys,json
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import process
ROOT=process.ROOT;D=ROOT/'detail_upgrade'
batches=json.loads((ROOT/'batches.json').read_text());jobs={}
seeded={'m432sa0','m432aa0','m432ab0'}
for parent,batch in batches.items():
 names=[n for n in batch['frames'] if n not in seeded];count=2 if parent=='identity' else 3
 for start in range(0,len(names),count):
  group=names[start:start+count];key=f'{parent}_detail_{start//count+1:02d}';natives=[];arts=[]
  for name in group:
   n=Image.new('RGBA',(576,576));n.paste(process.queue.native(ROOT,name).resize((512,512),Image.Resampling.NEAREST),(32,32));natives.append(n)
   p=ROOT/'registered_2x'/f'{name}.png'
   if p.exists():arts.append(Image.open(p).convert('RGBA'))
  boxes=[im.getchannel('A').getbbox() for im in natives+arts];crop=[min(b[0] for b in boxes)-12,min(b[1] for b in boxes)-12,max(b[2] for b in boxes)+12,max(b[3] for b in boxes)+12];w,h=crop[2]-crop[0],crop[3]-crop[1]
  def strip(images,path):
   out=Image.new('RGBA',(len(images)*w,h),(255,0,255,255))
   for i,im in enumerate(images):out.alpha_composite(im.crop(crop),(i*w,0))
   # Exact integer reference enlargement is layout preparation, not generated detail.
   out.convert('RGB').resize((out.width*2,out.height*2),Image.Resampling.NEAREST).save(path)
  strip(natives,D/'references'/f'{key}_native.png');refs=[f'references/{key}_native.png']
  if len(arts)==len(group):strip(arts,D/'references'/f'{key}_existing.png');refs.append(f'references/{key}_existing.png')
  refs.append('raw/identity_front_v1.png')
  prompt=f'''Use case: native sprite restoration and resolution/detail refinement. Restore these {len(group)} exact MM8 Dark Elf Warrior poses: {', '.join(group)}. Input 1 is the native pose, view, silhouette, color and relative-position authority, in {len(group)} equal columns and ONE row. Preserve every native head direction, torso angle, limb bend, foot lift, hand position and sword angle. All cells share a common native-coordinate crop and scale; preserve relative position, do not individually recenter or equalize figure heights.
'''
  if len(arts)==len(group):prompt+='Input 2 is the existing restored artwork in matching native coordinates. Retain its accepted character design and refine its raster detail, correcting any ambiguity only against input 1. Input 3 is the higher-detail accepted front identity, material and face reference only; its pose and view must not replace native action poses.\n'
  else:prompt+='Input 2 is the higher-detail accepted front identity, material and face reference only; its pose and view must not replace the native action poses.\n'
  prompt+='''Same adult male dark elf: dark reddish-brown face, pointed ears, swept-back silver-white hair, near-black armor, rounded studded shoulder plates, black gloves, green sleeve bands, ONE muted teal central chest disk and ONE muted green central back disk when visible, restrained gold fasteners, fitted black trousers, plated black boots and one very long narrow steel sword with gold hilt. Preserve native occlusion of chest/back disks by arms or torso rotation; do not invent extra teal circles on chest or shoulders. Preserve released sword positions in falling poses. Do not add equipment, glowing eyes, ornaments or anatomy.
Produce genuinely finer face, hair, finger, armor and boot detail at high resolution, with each upright head-to-feet body preferably at least 600 generated pixels. For low poses preserve body proportions and obtain comparable sampling along the body length. Keep the tight common layout in input 1 and its aspect ratio, with narrow existing empty margins, whole figures and sword tips intact. No enlarged empty canvas. Preserve dark native tonal weight and original material colors. Flat pure magenta background, no gradients, shadows, labels, borders or text. Only these exact poses, no extra cells or figures. Do not generate palette variants.
'''
  (D/'prompts'/f'{key}_v1.txt').write_text(prompt)
  jobs[key]={'parent_batch':parent,'frames':group,'columns':len(group),'rows':1,'native_canvas_crop_2x':crop,'reference_cell_size_px':[w*2,h*2],'references':refs,'prompt':f'prompts/{key}_v1.txt','status':'pending','minimum_generated_pixels_per_native_pixel':2.5}
p=D/'jobs.json';assert not p.exists(),'Do not overwrite resumable jobs';p.write_text(json.dumps({'schema_version':1,'seeded_trial_frames':sorted(seeded),'policy':'Compact common crops; generated sampling must exceed 2.5 pixels per native logical pixel and pass visible-detail review at runtime size. Native geometry unchanged.','jobs':jobs},indent=2)+'\n');print(len(jobs),'compact jobs;',sum(len(j['frames']) for j in jobs.values()),'frames plus 3 retained trials')
