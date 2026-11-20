import sys,json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path('level_generation/sprites/restoration_jobs').resolve()))
from finish import clean_solid,register_cell
from placement import inspect_placement
p=Path('level_generation/sprites/restoration_jobs/supplemental/noose_views')
raw=p/'raw.png'
if not raw.exists():shutil.copy2('/home/pjasicek/.codex/generated_images/01a0757a-c90b-7173-9d99-369ee5953200/exec-af5690c8-0029-4da7-a2f1-bde31bbdd009.png',raw)
im=Image.open(raw);layout=json.loads((p/'layout.json').read_text());reports={}
proofs={n:Image.new('RGB',(600,440),c) for n,c in [('light',(230,230,230)),('dark',(22,25,30))]}
for i,c in enumerate(layout['cells']):
 c['cell']=[i*256,0,(i+1)*256,768]
 bounds=[round(c['cell'][j]*im.size[j%2]/768) for j in range(4)]
 clean,stats=clean_solid(im.crop(bounds),(255,0,255))
 out,registration=register_cell(clean,layout,c,im.size)
 out.save(p/(c['name']+'.png'))
 native=Image.open(p/(c['name']+'.native.png'))
 report,warnings=inspect_placement(native,out)
 reports[c['name']]={'placement':report,'warnings':warnings,'cleanup':stats,'registration':registration,'sha256':hashlib.sha256((p/(c['name']+'.png')).read_bytes()).hexdigest()}
 for proof in proofs.values():
  for j,img in enumerate([native.resize((native.width*4,native.height*4),Image.Resampling.NEAREST),out.resize((out.width*2,out.height*2),Image.Resampling.NEAREST)]):
   proof.paste(img,(i*200+20+j*80,35),img)
  ImageDraw.Draw(proof).text((i*200+15,10),c['name']+' native / enhanced',fill=(130,130,130))
for name,img in proofs.items():img.save(p/('review_'+name+'.png'))
(p/'checks.json').write_text(json.dumps({'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'frames':reports},indent=2)+'\n')
print(json.dumps({n:{'delta':r['placement']['solid_bounds_delta'],'warnings':r['warnings']} for n,r in reports.items()}))
