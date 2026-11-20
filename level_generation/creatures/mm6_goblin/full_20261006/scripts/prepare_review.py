from pathlib import Path
from PIL import Image,ImageDraw
import json
O=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006');f=O/'review/final_playback';out=O/'review/final_contacts';out.mkdir(exist_ok=True)
records=[]
for clip in ['Standing','Walk','Attack','Hit','Death','Corpse','Fidget']:
 for view in ['front','right']:
  # These are decoded quarter-speed previews, not screenshots of a video player.
  files=sorted((f/'decoded'/f'{clip}_{view}'/'quarter_speed').glob('*.png'))
  assert files,(clip,view)
  for start in range(0,len(files),12):
   im=Image.new('RGB',(1440,1002),(35,35,35));d=ImageDraw.Draw(im)
   for j,p in enumerate(files[start:start+12]):
    x=(j%4)*360;y=(j//4)*334;frame=Image.open(p).convert('RGB');frame.thumbnail((360,300));im.paste(frame,(x,y+30));d.text((x+8,y+8),f'{clip} {view} #{start+j+1} source {(start+j)/48:.4f}s / slow {(start+j)/12:.4f}s',fill='white')
   name=f'{clip}_{view}_{start:03d}.jpg';im.save(out/name,quality=93);records.append({'file':name,'clip':clip,'view':view,'decoded_frames':[p.name for p in files[start:start+12]],'method':'Sequential decoded frames of the actual quarter-speed MP4; not real-time temporal viewing'})
(out/'index.json').write_text(json.dumps(records,indent=2)+'\n');print('Contact pages:',len(records))
