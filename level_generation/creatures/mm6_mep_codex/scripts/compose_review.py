"""Compose the measured final exports into reviewable contact sheets."""
from pathlib import Path
import json,csv
from PIL import Image,ImageDraw,ImageFont,ImageOps
P=Path(__file__).resolve().parents[1];out=P/'review/sheets';out.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
titlefont=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
def sheet(name,title,items,columns,cell=(300,400)):
 assert items and all(path.is_file() for path,label in items)
 w,h=cell;rows=(len(items)+columns-1)//columns
 canvas=Image.new('RGB',(columns*w,48+rows*(h+30)),(232,231,226));d=ImageDraw.Draw(canvas);d.text((12,10),title,font=titlefont,fill=(25,25,25))
 for i,(path,label) in enumerate(items):
  im=Image.open(path).convert('RGBA');im.thumbnail((w-8,h),Image.Resampling.LANCZOS);x=(i%columns)*w;y=48+(i//columns)*(h+30)
  canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2),im);d.text((x+8,y+h+5),label,font=font,fill=(25,25,25))
 canvas.save(out/name)
index=json.loads((P/'review/final_frames/index.json').read_text())
for role,record in index.items():
 items=[(P/f'review/final_frames/{role}_{view}_{i}.png',f'{view.replace("three_quarter","quarter")} {t:.3f}s') for view in record['views'] for i,t in enumerate(record['times'])]
 sheet(role+'.png','Mep / '+role+' / final runtime export',items,5)
playback=json.loads((P/'review/playback/playback.json').read_text());assert len(playback)==18
for role in index:
 items=[]
 for row in playback:
  if row['clip']!=role:continue
  assert len(row['frames'])==5
  for i,f in enumerate(row['frames']):items.append((P/'review/playback'/f['file'],f'{row["speed"]}x sample {i+1}'))
 sheet('playback_'+role+'.png','Mep / '+role+' / live 1x and 0.5x playback',items,5,(310,230))
sheet('tiers.png','Follower / Mystic / Fanatic of Baa',[(P/f'review/pbr/{t}_body.png',label) for t,label in zip('abc',['A / Follower','B / Mystic','C / Fanatic'])],3,(520,390))
sheet('face.png','Face / dedicated head texture',[(P/f'review/pbr/a_head_{v}.png','PBR '+v) for v in ['front','quarter']]+[(P/'review/final_frames/face_three_quarter.png','Texture detail')],3,(440,520))
sheet('hands.png','Actual exported hands and staff contact',[(P/f'review/final_frames/hand_{s}_{v}.png',s+' / '+v) for s in 'LR' for v in ['front','left','right','back']],4,(300,340))
sheet('staff.png','Native wooden walking staff / HD design and final asset',[(P/'references_hd/staff_design.png','Generated design'),(P/'review/final_frames/staff_three_quarter.png','Final staff'),(P/'review/final_frames/staff_detail_three_quarter.png','Wood detail'),(P/'review/final_frames/hand_R_front.png','Right hand grip')],4,(360,560))
sheet('actions_pbr.png','PBR / attack impact / cast launch / released staff',[(P/f'review/pbr/{f}.png',label) for f,label in [('a_attack','Attack 0.844 s'),('a_attack_side','Attack side'),('a_cast','Cast = Attack 0.844 s'),('a_cast_side','Cast side'),('a_dead','Dead'),('a_back','Standing back')]],3,(500,368))
items=[]
for view in range(8):
 for kind,label in [('ref','Unreduced'),('lod','Final LOD0')]:items.append((P/f'review/reduction/final_{kind}0_a_{view}.png',f'{view*45} deg / {label}'))
sheet('reduction_lod0.png','Initial production archive / reduction comparison',items,4,(280,280))
items=[]
for level,height in enumerate([700,550,220,88]):
 for view in [0,2,4,6]:items.append((P/f'review/reduction/final_lod{level}_a_{view}.png',f'LOD{level} / {height}px / {view*45} deg'))
sheet('lod_chain.png','Initial production archive / LOD chain',items,4,(260,260))
links=['# Final review evidence','', 'Death timing/playback uses the round-3 export; other accepted clips and PBR views remain from round 2. The four round1_* sheets and the reduction/LOD-chain sheets are historical. PBR and playback use the eight-influence review viewer.','']
links += [f'- [{f.stem}]({f.name})' for f in sorted(out.glob('*.png'))]
(out/'README.md').write_text('\n'.join(links)+'\n')
print('SHEETS',len(list(out.glob('*.png'))),flush=True)
