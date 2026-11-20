import json,sys,csv
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round6'
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
for view in ['front','three_quarter']:
 sheet=Image.new('RGB',(1800,850),'#deded9');dr=ImageDraw.Draw(sheet)
 for i,(stage,label)in enumerate([('round1','Round 1 bright ramp'),('current','Before round 6'),('new','Round 6 midpoint')]):
  sheet.paste(Image.open(R/f'steel_{stage}_{view}.png'),(600*i,50));dr.text((600*i+12,12),label,fill='#111111',font=font)
 sheet.save(R/f'steel_comparison_{view}.png')
sheet=Image.new('RGB',(1800,650),'#deded9');dr=ImageDraw.Draw(sheet)
for i,stage in enumerate(['round1','current','new']):sheet.paste(Image.open(R/f'axe_{stage}_three_quarter.png'),(600*i,50));dr.text((600*i+12,12),stage,fill='#111111',font=font)
sheet.save(R/'axe_steel_comparison.png')
for view in ['front','left','three_quarter']:
 rows=json.loads((P/f'review/final_{view}/frames.json').read_text());full=Image.new('RGB',(2240,3360));dr=ImageDraw.Draw(full)
 for j,row in enumerate(rows):
  for i,(path,label)in enumerate(row):full.paste(Image.open(path).convert('RGB'),(i*320,j*420));dr.text((i*320+4,j*420+4),label,fill='black')
 full.save(P/f'review/final_{view}.png')
 row=rows[2];sheet=Image.new('RGB',(2240,460),'#deded9');dr=ImageDraw.Draw(sheet)
 for i,(path,label)in enumerate(row):sheet.paste(Image.open(path).convert('RGB'),(i*320,40));dr.text((i*320+4,10),label,fill='black')
 sheet.save(R/f'running_{view}.png')
d=json.loads((R/'running_jitter.json').read_text());chart=Image.new('RGB',(1500,1080),'white');draw=ImageDraw.Draw(chart);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
for col,n in enumerate(['B_Pelvis','B_Head']):
 for row,(key,unit)in enumerate([('height_m','height m'),('velocity_m_s','velocity m/s'),('acceleration_m_s2','acceleration m/s2')]):
  x0=90+col*740;y0=75+row*340;w=610;h=240;values=[np.array(d[rev]['vertical'][n][key])for rev in ['before','after']];low=min(v.min()for v in values);high=max(v.max()for v in values);margin=(high-low)*.08;low-=margin;high+=margin
  draw.text((x0,y0-32),n+' / '+unit,fill='black',font=small)
  for k in range(5):
   y=y0+h*k/4;draw.line((x0,y,x0+w,y),fill='#dddddd');draw.text((x0-75,y-8),f'{high-(high-low)*k/4:.2f}',fill='black',font=small)
  for j,rev in enumerate(['before','after']):
   t=np.array(d[rev]['vertical'][n]['times_s']);t=t if row==0 else (t[:-1]+t[1:])/2 if row==1 else t[1:-1];points=[(x0+v/.8*w,y0+h-(z-low)/(high-low)*h)for v,z in zip(t,values[j])];draw.line(points,fill=['#a34136','#247c81'][j],width=3)
  draw.text((x0,y0+h+8),'0           0.2           0.4           0.6           0.8 seconds',fill='black',font=small)
draw.text((90,12),'48 Hz vertical motion: BEFORE (red) / STANDARD RUN (teal)',fill='black',font=font);chart.save(R/'vertical_motion.png')
(R/'README.md').write_text('''# Round 6 review

- `steel_comparison_front.png` / `steel_comparison_three_quarter.png`: round-1 bright ramp, pre-round-6 dark ramp, new midpoint, on identical accepted geometry and lighting. The archived round-1 ramp is used, not its obsolete prop geometry. Shield remains unchanged in every column.
- `axe_steel_comparison.png`: the same palette comparison on the accepted 796-triangle axe.
- `steel_luminance.json`: native armor ROIs and core steel-mask texel statistics (not projected surface-area averages), means and highlight percentiles in linear and sRGB spaces.
- `running_front.png`, `running_left.png`, `running_three_quarter.png`: fitted Standard Run. Full refreshed eight-clip sheets are one directory up.
- `vertical_motion.png`, `running_jitter.json`: 48 Hz positional diagnostics and the unchanged shared angular-jitter implementation. The shared runner has no positional acceleration threshold; no custom pass gate was added.
- `final/gates.md`: current shared Running gates; remaining inherited geometry/grip/posture failures are disclosed in HANDOFF.md.
- `artifact_parity.json`: unchanged geometry, seven unchanged clips, hashes and counts.
''')
