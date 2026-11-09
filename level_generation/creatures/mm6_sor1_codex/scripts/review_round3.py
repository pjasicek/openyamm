from pathlib import Path
import subprocess,json,sys
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1];url=json.loads((p/'work/viewer_server.json').read_text())['url'];out=p/'review/round3/browser';out.mkdir(exist_ok=True,parents=True)
r=subprocess.run(['node',str(p.parent/'claude_shared/check_viewer.mjs'),url],text=True,capture_output=True,check=True)
(p/'review/viewer_check.json').write_text(r.stdout);print('VIEWER CHECK PASS',flush=True)
m=json.loads((p/'review/viewer/manifest.json').read_text());specs=[]
for role,d in m['clips'].items():
 for i in range(9):specs.append(f'{role}_{i}:'.replace(':',':',1)+f'{role}:{d["duration"]*i/8}:quarter:body')
for role,t in [('Standing',0),('Walking',.15),('Attack',1.220833),('Cast',0.7375),('Hit',.14),('Death',.6),('Dead',0),('Fidget',1.1)]:
 for view in ['front','left']:specs.append(f'{role}_{view}:{role}:{t}:{view}:body')
for tier in 'abc':
 specs.extend([f'tier_{tier}:Standing:0:front:body:::sor1_{tier}',f'collar_{tier}:Standing:0:front:head:0,1.45,0.80:0,1.43,0:sor1_{tier}'])
specs += ['cast_hand:Cast:0.7375:quarter:arms:.9,1.45,.90:.30,1.20,.4:sor1_c','attack_grip:Attack:1.220833:quarter:arms:-.75,1.55,1.20:-.2,1.30,.4:sor1_c','free_hand:Standing:0:front:arms:.48,1.10,.62:.32,.95,.03:sor1_c','attack_collar:Attack:1.220833:front:head:0,1.65,.9:0,1.45,0:sor1_c']
for label,t in [('frame16',16/30),('frame20',20/30),('drive29',29/30),('drive47',47/30)]:
 for view in ['front','left','quarter']:specs.append(f'attack_{label}_{view}:Attack:{t}:{view}:arms')
for label,t in [('frame16_48fps',16/48),('frame20_48fps',20/48),('drive29_48fps',29/48),('drive47_48fps',47/48),('full_extension',1.45)]:
 for view in ['front','left','quarter']:specs.append(f'attack_{label}_{view}:Attack:{t}:{view}:arms')
subprocess.run(['node',str(p/'scripts/viewer_shots.mjs'),url,str(out),*specs],check=True)
for role in m['clips']:
 sheet=Image.new('RGB',(1440,1134),'white');draw=ImageDraw.Draw(sheet)
 for i in range(9):
  im=Image.open(out/f'{role}_{i}.png');im.thumbnail((480,350));x=(i%3)*480;y=(i//3)*378;sheet.paste(im,(x,y+25));draw.text((x+8,y+7),f'{role} {i}/8',fill='black')
 sheet.save(out/f'{role}_contact.jpg',quality=92)
subprocess.run(['node',str(p/'scripts/viewer_playback.mjs'),url,str(out)],check=True)
print('BROWSER REVIEW PASS',len(specs),'stills, 16 playback passes',flush=True)
