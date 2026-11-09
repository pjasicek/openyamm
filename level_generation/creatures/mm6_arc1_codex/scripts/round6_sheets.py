from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round6';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
# The current contact sheets use newly rendered shot poses at the shorter timestamps.
code=(P/'scripts/compose_sheets.py').read_text();exec(code[:code.index("for clip,t in")])
for role in ['Attack','Cast']:
 out=Image.new('RGB',(1200,650),'#292c30');draw=ImageDraw.Draw(out);draw.text((10,7),f'{role} 0.800s — unchanged release pose; right hand above, left below',font=font,fill='white')
 for j,side in enumerate('RL'):
  for i,view in enumerate('abcd'):out.paste(Image.open(P/f'review/hand_{role}1.2_{side}_{view}.png').convert('RGB'),(i*300,40+j*305))
 out.save(P/f'review/hands_{role}.jpg',quality=94)
R=P/'review/round6';d=json.loads((R/'loop_endpoints.json').read_text());out=Image.new('RGB',(1320,1730),'#292c30');draw=ImageDraw.Draw(out)
draw.text((15,10),'Review round 6 — exact loop endpoints; Running aliases Walking',font=font,fill='white')
for j,role in enumerate(['Walking','Standing','Fidget']):
 y=48+j*520;draw.text((15,y),f'{role}: all 63 joints: 0.000 mm / 0.000 degrees; local TRS + world matrices identical',font=small,fill='white')
 for i,(label,view)in enumerate([('first','front'),('last','front'),('first','left'),('last','left')]):
  out.paste(Image.open(R/f'{role}_{label}_{view}.png').convert('RGB'),(i*330,y+30));draw.text((i*330+10,y+474),f'{label} / {view}',font=font,fill='white')
draw.text((15,1620),'All three loops, near LOD, first = last sole heights (heel / toe, mm):',font=font,fill='white')
draw.text((15,1648),'Left: 3.494 / 4.483; Right: 3.142 / 4.412. Running uses the same Walking data.',font=font,fill='white')
draw.text((15,1677),'Walking last 48 Hz sample (0.791667s): Left 3.267 / 4.379; Right 5.037 / 6.219 mm.',font=small,fill='white')
out.save(R/'loop_comparison.jpg',quality=93)
# Concise side-view speed comparison. Old and new phases are the same poses.
frames=json.loads((P/'review/clips/frames.json').read_text());out=Image.new('RGB',(1800,530),'#292c30');draw=ImageDraw.Draw(out)
draw.text((12,8),'Review round 6 — Attack = Cast; 1.5x speed, feet planted, release 0.800s',font=font,fill='white')
for i,index in enumerate([0,2,4,5,6,8]):
 row=[r for r in frames['Attack']if r['view']=='left'][index];out.paste(Image.open(P/row['path']).convert('RGB'),(i*300,42));draw.text((i*300+8,466),f'R5 {row["seconds"]*1.5:.3f}s -> R6 {row["seconds"]:.3f}s',font=small,fill='white')
draw.text((12,505),'Visible LODs: heel/toe <= 5.181 mm; sole tilt <= 0.940 degrees; no floor penetration.',font=small,fill='white');out.save(R/'attack_timing_comparison.jpg',quality=93)
