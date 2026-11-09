"""Refresh the changed Walking evidence; other seven action buffers are byte-identical (parity receipt)."""
from pathlib import Path
import json,subprocess,sys
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1];url=json.loads((p/'work/viewer_server.json').read_text())['url'];out=p/'review/round2/browser'
subprocess.run([sys.executable,str(p/'scripts/sheets.py'),'final_clips'],check=True)
r=subprocess.run(['node',str(p.parent/'claude_shared/check_viewer.mjs'),url],capture_output=True,text=True,check=True);(p/'review/viewer_check.json').write_text(r.stdout);print('VIEWER CHECK PASS',flush=True)
prior=json.loads((out/'skinning_check.json').read_text());specs=[f'Walking_{i}:Walking:{.8*i/8}:quarter:body' for i in range(9)]+[f'Walking_{v}:Walking:.15:{v}:body' for v in ['front','left']]
subprocess.run(['node',str(p/'scripts/viewer_shots.mjs'),url,str(out),*specs],check=True)
now=json.loads((out/'skinning_check.json').read_text());prior['models'].update(now['models']);prior['walking_refresh_passed']=True;(out/'skinning_check.json').write_text(json.dumps(prior,indent=2))
sheet=Image.new('RGB',(1440,1134),'white');draw=ImageDraw.Draw(sheet)
for i in range(9):
 im=Image.open(out/f'Walking_{i}.png');im.thumbnail((480,350));x=i%3*480;y=i//3*378;sheet.paste(im,(x,y+25));draw.text((x+8,y+7),f'Walking {i}/8',fill='black')
sheet.save(out/'Walking_contact.jpg',quality=92)
subprocess.run(['node',str(p/'scripts/viewer_playback.mjs'),url,str(out)],check=True)
print('FINAL REVIEW PASS',flush=True)
