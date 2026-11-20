import json,sys
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent
root=p.parents[2]
sys.path.insert(0,str(root))
from finish import check_existing
job=json.loads((root/'jobs/g08065_v0_s0.json').read_text())
sources=json.loads((root/'sources.json').read_text())
backup=p/'before_cloth_registration';backup.mkdir(exist_ok=True)
for cell in job['cells']:
 name=cell['asset']+'.png';src=backup/name
 if not src.exists():src.write_bytes((p/name).read_bytes())
 im=Image.open(src).convert('RGBA');hinge=128
 cloth=im.crop((hinge,0,im.width,im.height)).convert('RGBa')
 cloth=cloth.resize((round(cloth.width*.95),cloth.height),Image.Resampling.LANCZOS).convert('RGBA')
 out=Image.new('RGBA',im.size);out.paste(im.crop((0,0,hinge,im.height)),(0,0));out.paste(cloth,(hinge,0));out.save(p/name)
check_existing(job,sources,p)
group=next(g for g in json.loads((root/'groups.json').read_text()) if g['name']==job['group'])
tl=group['tracks'][0]['timeline'];sheet=Image.new('RGB',(180*len(tl),570),(35,40,37));d=ImageDraw.Draw(sheet)
for i,t in enumerate(tl):
 d.text((i*180+6,5),f"{t['image']} {t['duration_ms']:g}ms",fill='white')
 for row,src in enumerate([root/'native'/(t['asset']+'.png'),p/(t['asset']+'.png')]):
  im=Image.open(src).convert('RGBA');im.thumbnail((170,256));sheet.paste(im,(i*180+(180-im.width)//2,25+row*275),im)
sheet.save(p/'timed_contact.png')
