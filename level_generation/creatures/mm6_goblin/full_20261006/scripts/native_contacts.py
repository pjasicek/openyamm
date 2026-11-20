from pathlib import Path
from PIL import Image,ImageDraw
import json
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');R=O.parent;D=O/'review/source_comparisons';D.mkdir(exist_ok=True)
spec=json.loads((R/'stage1_20261006/motion_spec.json').read_text());records=[]
for c in spec['clips']:
 views=['front','quarter','right','rear_quarter','back'] if c['name'] in ['Standing','Walk'] else ['front']
 for vi,view in enumerate(views):
  sheet=Image.new('RGB',(1420,972),(38,38,38));draw=ImageDraw.Draw(sheet)
  for i,a in enumerate(c['anchors']):
   source=R/'stage1_20261006'/a['source_images'][vi];n=Image.open(source).convert('RGBA');bg=Image.new('RGBA',n.size,(85,85,85,255));bg.alpha_composite(n);n=bg.convert('RGB')
   frame=1+int(a['time_ms']*48/1000)
   if c['name'] in ['Standing','Walk']:model=O/'review/final_native_views'/f'{c["name"]}_{frame:02d}_{view}.png'
   else:model=O/'review/final_playback'/('frames_'+c['name']+'_'+view)/f'{frame-1:03d}.png'
   m=Image.open(model).convert('RGB').resize((355,289),Image.Resampling.LANCZOS)
   x=(i%2)*710;y=(i//2)*324;sheet.paste(n,(x,y+30));sheet.paste(m,(x+355,y+30));draw.text((x+5,y+6),f'{c["name"]} {view} {a["time_ms"]}ms: native | final HD',fill='white')
   records.append({'clip':c['name'],'view':view,'native_time_ms':a['time_ms'],'source':str(source.relative_to(R)),'model':str(model.relative_to(R)),'camera':'Fixed 355x289 native canvas and height; native stored 45 degree diagonal views for Standing/Walk'})
  sheet.save(D/f'{c["name"]}_{view}.jpg',quality=94)
(D/'index.json').write_text(json.dumps(records,indent=2)+'\n');print('Native/model comparisons:',len(records))
